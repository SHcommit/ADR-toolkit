"""Change an ADR's status through the deterministic lifecycle state machine."""
from pathlib import Path

from scripts.core import constraints
from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.lifecycle import InvalidTransitionError, validate_transition


def run(args) -> dict:
    adr_dir = Path(args.dir)
    target_file = identifiers.find_by_number(adr_dir, args.adr_number)

    if target_file is None:
        return {
            "ok": False,
            "operation": "status",
            "errors": [{"code": "ADR_NOT_FOUND", "id": args.adr_number}],
        }

    try:
        data, body = fm.parse(target_file.read_text(encoding="utf-8"))
    except fm.FrontmatterError as exc:
        return {
            "ok": False,
            "operation": "status",
            "errors": [{"code": "BAD_FRONTMATTER", "file": target_file.name, "detail": str(exc)}],
        }

    try:
        validate_transition(data.get("status"), args.to)
    except InvalidTransitionError as exc:
        return {
            "ok": False,
            "operation": "status",
            "errors": [{"code": "INVALID_TRANSITION", "detail": str(exc)}],
        }

    # Constraints only get enforced by CHECK once an ADR is accepted, so
    # that's the one transition where a malformed block would otherwise go
    # silently unenforced (docs/adr-toolkit-audit-report.md §2.5 5.2).
    warnings = constraints.lint(body) if args.to == "accepted" else []

    if getattr(args, "dry_run", False):
        return {
            "ok": True,
            "operation": "status",
            "dry_run": True,
            "would_update": str(target_file),
            "to": args.to,
            "warnings": warnings,
        }

    data["status"] = args.to
    target_file.write_text(
        fm.serialize(data, body, body_is_parsed=True), encoding="utf-8"
    )

    return {
        "ok": True,
        "operation": "status",
        "dry_run": False,
        "updated": str(target_file),
        "to": args.to,
        "warnings": warnings,
    }
