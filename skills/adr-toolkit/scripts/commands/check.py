"""Match a git diff against Accepted ADRs' constraints: rules and
Superseded ADRs' affected_paths, per §7/§16 of the design spec."""
import re
from pathlib import Path

from scripts.commands import diff as diff_command
from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.constraints import ConstraintsError, extract_constraints
from scripts.core.git_paths import GitPathsError, list_existing_paths
from scripts.rules import conflict

SKIP_FILES = {"README.md", "adr-template.md"}
RESOLUTIONS = ["fix_code", "supersede_adr", "adjust_scope", "register_exception", "false_positive"]

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
    adr_dir = Path(args.dir)
    if not adr_dir.is_absolute():
        adr_dir = root / adr_dir
    if not adr_dir.is_dir():
        # Silently proceeding here would emit a confident "no conflicts" for
        # what is really a configuration error.
        return {
            "ok": False,
            "operation": "check",
            "errors": [{"code": "ADR_DIR_NOT_FOUND", "path": str(adr_dir)}],
        }

    entries, warnings = _load_adrs(adr_dir)

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

    return {
        "ok": True,
        "operation": "check",
        "diff": {"mode": diff_result["mode"], "ref": diff_result.get("ref"), "files_changed": len(diff_files)},
        "findings": findings,
        "warnings": warnings,
    }


def _load_adrs(adr_dir: Path) -> tuple:
    entries, warnings = [], []
    for entry in sorted(adr_dir.glob("*.md")):
        if entry.name in SKIP_FILES or identifiers.parse_filename(entry.name) is None:
            continue
        try:
            data, body = fm.parse(entry.read_text(encoding="utf-8"))
        except (fm.FrontmatterError, OSError, UnicodeDecodeError) as exc:
            warnings.append({"code": "BAD_FRONTMATTER", "file": entry.name, "detail": str(exc)})
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
