"""Match a git diff against Accepted ADRs' constraints: rules and
Superseded ADRs' affected_paths, per §7/§16 of the design spec."""
import json
import re
from datetime import date
from pathlib import Path

from scripts.commands import diff as diff_command
from scripts.core import frontmatter as fm
from scripts.core.adr_directory import iter_adr_files
from scripts.core.constraints import ConstraintsError, extract_constraints
from scripts.core.exceptions import applies_to, is_expired, validate_exception
from scripts.core.git_paths import GitPathsError, list_existing_paths
from scripts.core.repository_paths import resolve_from_root
from scripts.core.schema import validate_frontmatter
from scripts.rules import conflict

RESOLUTIONS = ["fix_code", "supersede_adr", "adjust_scope", "register_exception", "false_positive"]

# The stable, machine-readable confidence contract documented in README.md's
# "CHECK confidence" section and references/conflict-rules.md — promotes the
# ad-hoc `kind` values below into the four values agents are told to report.
CONFIDENCE_BY_KIND = {
    "related": "VERIFIED",
    "verified_violation": "VIOLATED",
    "review_required": "UNVERIFIABLE",
    "no_applicable_constraint": "UNVERIFIABLE",
}

# Every ADR this toolkit writes uses `## Confirmation` (templates/madr-*.md and
# commands/create.py); `## Verification` is the design spec's name for the same
# section. Accept both, plus any trailing words in the heading.
VERIFICATION_HEADING_RE = re.compile(
    r"^#+\s*(?:Verification|Confirmation)\b.*$", re.IGNORECASE | re.MULTILINE
)
NEXT_HEADING_RE = re.compile(r"^#+\s", re.MULTILINE)
PATH_TOKEN_RE = re.compile(r"`([^`]+\.[a-zA-Z0-9]+)`")


def run(args) -> dict:
    diff_result = diff_command.run(args)
    if not diff_result["ok"]:
        return {"ok": False, "operation": "check", "errors": diff_result["errors"]}
    diff_files = diff_result["files"]

    root = Path(getattr(args, "root", ".")).resolve()
    try:
        existing_paths = list_existing_paths(root)
    except GitPathsError as exc:
        return {
            "ok": False,
            "operation": "check",
            "errors": [{"code": "GIT_LS_FILES_FAILED", "detail": str(exc)}],
        }

    # `--dir` is relative to `--root`, so `check --root /repo --dir docs/decisions`
    # means the same directory no matter what the process CWD happens to be.
    adr_dir = resolve_from_root(root, args.dir)
    if not adr_dir.is_dir():
        # Silently proceeding here would emit a confident "no conflicts" for
        # what is really a configuration error.
        return {
            "ok": False,
            "operation": "check",
            "errors": [{"code": "ADR_DIR_NOT_FOUND", "path": str(adr_dir)}],
        }

    entries, warnings = _load_adrs(adr_dir)
    active_exceptions, exception_warnings = _load_exceptions(adr_dir)
    warnings += exception_warnings

    findings = []
    for entry in entries:
        data, body = entry["data"], entry["body"]
        if data.get("status") != "accepted":
            continue
        if not conflict.affected_paths_overlap(diff_files, data.get("affected_paths", [])):
            continue

        adr_id = data.get("id")
        try:
            rules = extract_constraints(body)
        except ConstraintsError as exc:
            warnings.append({"code": "BAD_CONSTRAINTS", "adr_id": adr_id, "detail": str(exc)})
            rules = []

        produced_any = False
        for rule in rules:
            try:
                violation = conflict.evaluate_rule(rule, diff_files, existing_paths)
            except re.error as exc:
                # A malformed regex in one ADR's `pattern` must not abort the
                # whole run — degrade to the same BAD_CONSTRAINTS warning a
                # malformed constraints block already produces.
                warnings.append({
                    "code": "BAD_CONSTRAINTS",
                    "adr_id": adr_id,
                    "rule_id": rule.get("id"),
                    "detail": f"Invalid regex in rule pattern: {exc}",
                })
                continue
            if violation:
                findings.append({**violation, "adr_id": adr_id, "resolutions": RESOLUTIONS})
                produced_any = True

        review = _missing_realization(body, diff_files, existing_paths)
        if review:
            findings.append({"adr_id": adr_id, "kind": "review_required", **review})
            produced_any = True

        if not produced_any:
            findings.append({"adr_id": adr_id, "kind": "related" if rules else "no_applicable_constraint"})

    for entry in entries:
        data = entry["data"]
        if data.get("status") != "superseded":
            continue
        if not conflict.affected_paths_overlap(diff_files, data.get("affected_paths", [])):
            continue
        findings.append({
            "adr_id": data.get("id"),
            "kind": "verified_violation",
            "rule_id": "superseded_reference",
            "severity": "major",
            "message": (
                f"This path is governed by {data.get('id')}, which is superseded "
                f"by {data.get('superseded_by')}. Review the replacement decision "
                f"before proceeding."
            ),
            "file": None,
            "evidence": {"superseded_by": data.get("superseded_by")},
            "resolutions": RESOLUTIONS,
        })

    for finding in findings:
        finding["confidence"] = CONFIDENCE_BY_KIND[finding["kind"]]
        if finding["kind"] == "verified_violation":
            match = _matching_exception(
                active_exceptions,
                adr_id=finding.get("adr_id"),
                rule_id=finding.get("rule_id"),
                file_path=finding.get("file"),
            )
            # Annotate only — an exception never hides or downgrades a
            # violation. Confidence stays VIOLATED; a human/agent still sees
            # and reports it, now with the approved exception attached.
            if match is not None:
                finding["exception"] = {
                    "id": match["id"],
                    "owner": match["owner"],
                    "reason": match["reason"],
                    "expiry": match["expiry"],
                }

    return {
        "ok": True,
        "operation": "check",
        "diff": {"mode": diff_result["mode"], "ref": diff_result.get("ref"), "files_changed": len(diff_files)},
        "findings": findings,
        "warnings": warnings,
    }


def _load_exceptions(adr_dir: Path) -> tuple:
    """Load active (non-expired, schema-valid) exceptions from adr_dir/exceptions.

    A malformed exception file degrades to a warning, same as a malformed ADR
    — it must never silently vanish, and it must never abort the whole run.
    """
    exceptions_dir = adr_dir / "exceptions"
    active, warnings = [], []
    if not exceptions_dir.is_dir():
        return active, warnings
    for path in sorted(exceptions_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
            warnings.append({"code": "BAD_EXCEPTION", "file": path.name, "detail": str(exc)})
            continue
        schema_errors = validate_exception(data) if isinstance(data, dict) else ["not a JSON object"]
        if schema_errors:
            warnings.extend({
                "code": "BAD_EXCEPTION", "file": path.name, "detail": detail,
            } for detail in schema_errors)
            continue
        if is_expired(data["expiry"], today=date.today()):
            continue
        active.append(data)
    return active, warnings


def _matching_exception(exceptions: list, *, adr_id: str, rule_id: str, file_path):
    for exception in exceptions:
        if applies_to(exception, adr_id=adr_id, rule_id=rule_id, file_path=file_path):
            return exception
    return None


def _load_adrs(adr_dir: Path) -> tuple:
    entries, warnings = [], []
    for entry, parsed in iter_adr_files(adr_dir):
        if parsed is None:
            continue
        try:
            data, body = fm.parse(entry.read_text(encoding="utf-8"))
        except (fm.FrontmatterError, OSError, UnicodeDecodeError) as exc:
            warnings.append({"code": "BAD_FRONTMATTER", "file": entry.name, "detail": str(exc)})
            continue
        schema_errors = validate_frontmatter(data)
        if schema_errors:
            warnings.extend({
                "code": "SCHEMA_ERROR",
                "file": entry.name,
                "detail": detail,
            } for detail in schema_errors)
            continue
        entries.append({"data": data, "body": body})
    return entries, warnings


def _missing_realization(body: str, diff_files: list, existing_paths: set):
    heading = VERIFICATION_HEADING_RE.search(body)
    if not heading:
        return None
    next_heading = NEXT_HEADING_RE.search(body, heading.end())
    section = body[heading.end():next_heading.start() if next_heading else len(body)]

    referenced_paths = PATH_TOKEN_RE.findall(section)
    if not referenced_paths:
        return None

    by_path = {f["path"]: f for f in diff_files}
    # §16.3: fire when a referenced path is removed OR was never created.
    missing = [
        p for p in referenced_paths
        if by_path.get(p, {}).get("change_type") == "deleted" or p not in existing_paths
    ]
    if not missing:
        return None

    return {
        "message": (
            f"Verification references {missing} which this diff removes "
            f"or which was never created."
        ),
        "evidence": {"unrealized_paths": missing},
    }
