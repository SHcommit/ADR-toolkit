"""Assign the next ADR ID and write a new ADR file from an approved draft."""
import json
from datetime import date
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.schema import validate_frontmatter

REQUIRED_DRAFT_FIELDS = {"title", "status", "body"}


def run(args) -> dict:
    draft_path = Path(args.input)
    adr_dir = Path(args.dir)
    dry_run = getattr(args, "dry_run", False)

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    missing = REQUIRED_DRAFT_FIELDS - draft.keys()
    if missing:
        return {
            "ok": False,
            "operation": "create",
            "errors": [{"code": "MISSING_DRAFT_FIELD", "fields": sorted(missing)}],
        }

    next_num = identifiers.next_id(adr_dir)
    slug = identifiers.slugify(draft["title"])
    filename = identifiers.format_filename(next_num, slug)
    target = adr_dir / filename

    if target.exists():
        return {
            "ok": False,
            "operation": "create",
            "errors": [{"code": "FILE_ALREADY_EXISTS", "path": str(target)}],
        }

    frontmatter_data = {
        "id": f"ADR-{next_num:04d}",
        "title": draft["title"],
        "status": draft["status"],
        "date": draft.get("date") or date.today().isoformat(),
        "decision_makers": draft.get("decision_makers", []),
        "related": draft.get("related", []),
        "affected_paths": draft.get("affected_paths", []),
        "tags": draft.get("tags", []),
        "retrospective": draft.get("retrospective", False),
    }

    schema_errors = validate_frontmatter(frontmatter_data)
    if schema_errors:
        return {
            "ok": False,
            "operation": "create",
            "errors": [{"code": "SCHEMA_ERROR", "detail": e} for e in schema_errors],
        }

    content = fm.serialize(frontmatter_data, draft["body"].strip() + "\n")

    if dry_run:
        return {"ok": True, "operation": "create", "dry_run": True, "would_create": str(target), "id": frontmatter_data["id"]}

    adr_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return {
        "ok": True,
        "operation": "create",
        "dry_run": False,
        "created": str(target),
        "id": frontmatter_data["id"],
    }
