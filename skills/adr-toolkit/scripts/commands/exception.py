"""Validate and record a CHECK policy exception (owner/reason/scope/expiry)."""
import json
from datetime import date
from pathlib import Path

from scripts.core import atomic_io
from scripts.core.exceptions import validate_exception
from scripts.core.repository_paths import resolve_from_root

REQUIRED_DRAFT_FIELDS = {"adr_id", "rule_id", "owner", "reason", "scope", "expiry"}


def _build_exception(draft: dict, exception_id: str) -> dict:
    return {
        "id": exception_id,
        "adr_id": draft["adr_id"],
        "rule_id": draft["rule_id"],
        "owner": draft["owner"],
        "reason": draft["reason"],
        "scope": draft["scope"],
        "expiry": draft["expiry"],
        "created": draft.get("created") or date.today().isoformat(),
    }


def _next_id(exceptions_dir: Path) -> int:
    existing = []
    if exceptions_dir.is_dir():
        for entry in exceptions_dir.glob("*.json"):
            if entry.stem.isdigit():
                existing.append(int(entry.stem))
    return max(existing, default=0) + 1


def run(args) -> dict:
    dry_run = getattr(args, "dry_run", False)
    root = Path(getattr(args, "root", "."))
    input_path = getattr(args, "input", None)

    if not input_path:
        return {"ok": False, "operation": "exception", "errors": [{"code": "MISSING_INPUT"}]}

    try:
        raw_draft = Path(input_path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return {
            "ok": False,
            "operation": "exception",
            "errors": [{"code": "DRAFT_FILE_NOT_FOUND", "path": input_path}],
        }
    try:
        draft = json.loads(raw_draft)
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "operation": "exception",
            "errors": [{"code": "DRAFT_FILE_INVALID_JSON", "path": input_path, "detail": str(exc)}],
        }

    missing = REQUIRED_DRAFT_FIELDS - draft.keys()
    if missing:
        return {
            "ok": False,
            "operation": "exception",
            "errors": [{"code": "MISSING_DRAFT_FIELD", "fields": sorted(missing)}],
        }

    adr_dir = resolve_from_root(root, args.dir)
    exceptions_dir = adr_dir / "exceptions"

    # Validate against a preview ID first. This must not touch disk -- not
    # even to create exceptions_dir or a lock file -- so a SCHEMA_ERROR and
    # a dry run both leave the filesystem untouched. Validity never depends
    # on which sequential number gets assigned (the ID always matches
    # EXC-NNNN by construction), so this result stays correct even if a
    # concurrent writer changes the real next number before the write below.
    preview_num = _next_id(exceptions_dir)
    preview_id = f"EXC-{preview_num:04d}"
    schema_errors = validate_exception(_build_exception(draft, preview_id))
    if schema_errors:
        return {
            "ok": False,
            "operation": "exception",
            "errors": [{"code": "SCHEMA_ERROR", "detail": e} for e in schema_errors],
        }

    if dry_run:
        target = exceptions_dir / f"{preview_num:04d}.json"
        return {
            "ok": True,
            "operation": "exception",
            "dry_run": True,
            "would_create": str(target),
            "id": preview_id,
        }

    with atomic_io.adr_directory_lock(exceptions_dir):
        next_num = _next_id(exceptions_dir)
        exception_id = f"EXC-{next_num:04d}"
        data = _build_exception(draft, exception_id)
        target = exceptions_dir / f"{next_num:04d}.json"
        atomic_io.atomic_write_text(target, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

        return {
            "ok": True,
            "operation": "exception",
            "dry_run": False,
            "created": str(target),
            "id": exception_id,
        }
