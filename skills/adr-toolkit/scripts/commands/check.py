"""Match a git diff against Accepted ADRs' constraints: rules and
Superseded ADRs' affected_paths, per §7/§16 of the design spec."""
from pathlib import Path

from scripts.commands import diff as diff_command
from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.constraints import ConstraintsError, extract_constraints
from scripts.rules import conflict

SKIP_FILES = {"README.md", "adr-template.md"}
RESOLUTIONS = ["fix_code", "supersede_adr", "adjust_scope", "register_exception", "false_positive"]


def run(args) -> dict:
    diff_result = diff_command.run(args)
    if not diff_result["ok"]:
        return {"ok": False, "operation": "check", "errors": diff_result["errors"]}
    diff_files = diff_result["files"]

    root = Path(getattr(args, "root", ".")).resolve()
    existing_paths = _existing_paths(root)

    adr_dir = Path(args.dir)
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
            violation = conflict.evaluate_rule(rule, diff_files, existing_paths)
            if violation:
                findings.append({**violation, "adr_id": adr_id, "resolutions": RESOLUTIONS})
                produced_any = True

        if not produced_any:
            findings.append({"adr_id": adr_id, "kind": "related" if rules else "no_applicable_constraint"})

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


def _existing_paths(root: Path) -> set:
    paths = set()
    for entry in root.rglob("*"):
        if not entry.is_file():
            continue
        relative = entry.relative_to(root)
        if ".git" in relative.parts:
            continue
        paths.add(relative.as_posix())
    return paths
