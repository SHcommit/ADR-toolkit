"""Validate and record a CHECK policy exception (owner/reason/scope/expiry)."""
import json
from datetime import date
from pathlib import Path

from scripts.core.exceptions import validate_exception
from scripts.core.repository_paths import resolve_from_root

REQUIRED_DRAFT_FIELDS = {"adr_id", "rule_id", "owner", "reason", "scope", "expiry"}


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
    next_num = _next_id(exceptions_dir)
    exception_id = f"EXC-{next_num:04d}"

    data = {
        "id": exception_id,
        "adr_id": draft["adr_id"],
        "rule_id": draft["rule_id"],
        "owner": draft["owner"],
        "reason": draft["reason"],
        "scope": draft["scope"],
        "expiry": draft["expiry"],
        "created": draft.get("created") or date.today().isoformat(),
    }

    schema_errors = validate_exception(data)
    if schema_errors:
        return {
            "ok": False,
            "operation": "exception",
            "errors": [{"code": "SCHEMA_ERROR", "detail": e} for e in schema_errors],
        }

    target = exceptions_dir / f"{next_num:04d}.json"

    if dry_run:
        return {
            "ok": True,
            "operation": "exception",
            "dry_run": True,
            "would_create": str(target),
            "id": exception_id,
        }

    exceptions_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "operation": "exception",
        "dry_run": False,
        "created": str(target),
        "id": exception_id,
    }
