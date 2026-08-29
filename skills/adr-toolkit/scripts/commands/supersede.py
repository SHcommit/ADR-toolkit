"""Mark one ADR as superseded by another and update both link directions."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.lifecycle import InvalidTransitionError, validate_transition


def run(args) -> dict:
    adr_dir = Path(args.dir)
    old_file = identifiers.find_by_number(adr_dir, args.adr_number)
    new_file = identifiers.find_by_number(adr_dir, args.by)

    if old_file is None:
        return {
            "ok": False,
            "operation": "supersede",
            "errors": [{"code": "ADR_NOT_FOUND", "id": args.adr_number}],
        }
    if new_file is None:
        return {
            "ok": False,
            "operation": "supersede",
            "errors": [{"code": "ADR_NOT_FOUND", "id": args.by}],
        }
    if args.adr_number == args.by or old_file.resolve() == new_file.resolve():
        return {
            "ok": False,
            "operation": "supersede",
            "errors": [{
                "code": "SELF_SUPERSEDE",
                "detail": "An ADR cannot supersede itself.",
                "id": args.adr_number,
            }],
        }

    old_text = old_file.read_text(encoding="utf-8")
    old_data, old_body = fm.parse(old_text)
    try:
        validate_transition(old_data["status"], "superseded")
    except InvalidTransitionError as exc:
        return {
            "ok": False,
            "operation": "supersede",
            "errors": [{"code": "INVALID_TRANSITION", "detail": str(exc)}],
        }

    if getattr(args, "dry_run", False):
        return {
            "ok": True,
            "operation": "supersede",
            "dry_run": True,
            "would_update": [str(old_file), str(new_file)],
        }

    new_data, new_body = fm.parse(new_file.read_text(encoding="utf-8"))
    old_data["status"] = "superseded"
    old_data["superseded_by"] = new_data["id"]

    supersedes = []
    for adr_id in new_data.get("supersedes", []) + [old_data["id"]]:
        if adr_id not in supersedes:
            supersedes.append(adr_id)
    new_data["supersedes"] = supersedes

    old_output = fm.serialize(old_data, old_body, body_is_parsed=True)
    new_output = fm.serialize(new_data, new_body, body_is_parsed=True)

    old_file.write_text(old_output, encoding="utf-8")
    try:
        new_file.write_text(new_output, encoding="utf-8")
    except Exception:
        # Preserve the original failure while making the completed first write recoverable.
        try:
            old_file.write_text(old_text, encoding="utf-8")
        except Exception:
            pass
        raise

    return {
        "ok": True,
        "operation": "supersede",
        "dry_run": False,
        "old": old_data["id"],
        "new": new_data["id"],
    }
