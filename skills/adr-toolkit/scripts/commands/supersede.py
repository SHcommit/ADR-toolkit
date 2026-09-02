"""Mark one ADR as superseded by another and update both link directions."""
from pathlib import Path

from scripts.core import atomic_io
from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.lifecycle import InvalidTransitionError, validate_transition


def run(args) -> dict:
    adr_dir = Path(args.dir)

    with atomic_io.adr_directory_lock(adr_dir):
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
        new_text = new_file.read_text(encoding="utf-8")
        try:
            old_data, old_body = fm.parse(old_text)
        except fm.FrontmatterError as exc:
            return {
                "ok": False,
                "operation": "supersede",
                "errors": [{"code": "BAD_FRONTMATTER", "file": old_file.name, "detail": str(exc)}],
            }
        try:
            new_data, new_body = fm.parse(new_text)
        except fm.FrontmatterError as exc:
            return {
                "ok": False,
                "operation": "supersede",
                "errors": [{"code": "BAD_FRONTMATTER", "file": new_file.name, "detail": str(exc)}],
            }

        missing_ids = [
            number for number, data in ((args.adr_number, old_data), (args.by, new_data))
            if not data.get("id")
        ]
        if missing_ids:
            return {
                "ok": False,
                "operation": "supersede",
                "errors": [{
                    "code": "BAD_FRONTMATTER",
                    "detail": "ADR file is missing a required 'id' field",
                    "ids": missing_ids,
                }],
            }

        try:
            validate_transition(old_data.get("status"), "superseded")
        except InvalidTransitionError as exc:
            return {
                "ok": False,
                "operation": "supersede",
                "errors": [{"code": "INVALID_TRANSITION", "detail": str(exc)}],
            }

        if new_data.get("status") != "accepted":
            return {
                "ok": False,
                "operation": "supersede",
                "errors": [{
                    "code": "INVALID_SUPERSEDING_STATUS",
                    "detail": (
                        f"Superseding ADR {new_data['id']} must have status 'accepted', "
                        f"found {new_data.get('status')!r}."
                    ),
                    "id": args.by,
                }],
            }

        if getattr(args, "dry_run", False):
            return {
                "ok": True,
                "operation": "supersede",
                "dry_run": True,
                "would_update": [str(old_file), str(new_file)],
            }

        old_data["status"] = "superseded"
        old_data["superseded_by"] = new_data["id"]

        supersedes = []
        for adr_id in new_data.get("supersedes", []) + [old_data["id"]]:
            if adr_id not in supersedes:
                supersedes.append(adr_id)
        new_data["supersedes"] = supersedes

        old_output = fm.serialize(old_data, old_body, body_is_parsed=True)
        new_output = fm.serialize(new_data, new_body, body_is_parsed=True)

        atomic_io.atomic_write_text(old_file, old_output)
        try:
            atomic_io.atomic_write_text(new_file, new_output)
        except Exception as write_exc:
            # atomic_write_text already guarantees old_file is never torn by
            # a crash; this additionally restores its *content* to the
            # pre-supersede value so the two files stay a matched pair when
            # the second write fails outright (as opposed to the process
            # being killed, which atomic_write_text protects against on its
            # own without needing this rollback).
            try:
                atomic_io.atomic_write_text(old_file, old_text)
            except Exception as rollback_exc:
                raise RuntimeError(
                    f"Failed to write {new_file} ({write_exc!r}); rollback of {old_file} also "
                    f"failed ({rollback_exc!r}); {old_file} may be left in an inconsistent state"
                ) from write_exc
            raise

        return {
            "ok": True,
            "operation": "supersede",
            "dry_run": False,
            "old": old_data["id"],
            "new": new_data["id"],
        }
