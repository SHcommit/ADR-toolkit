"""Validate ADR directory structural integrity: IDs, frontmatter, and links."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.config import ConfigError, load_repository_config
from scripts.core.schema import validate_frontmatter
from scripts.core.repository_paths import resolve_from_root

SKIP_FILES = {"README.md", "adr-template.md"}


def run(args) -> dict:
    root = Path(getattr(args, "root", "."))
    adr_dir = resolve_from_root(root, args.dir)
    errors = []

    try:
        load_repository_config(root)
    except ConfigError as exc:
        return {
            "ok": False,
            "operation": "validate",
            "checked": 0,
            "errors": [{"code": "CONFIG_ERROR", "detail": str(exc)}],
        }

    adr_files = sorted(p for p in adr_dir.glob("*.md") if p.name not in SKIP_FILES)

    parsed_entries = []
    seen_ids: dict = {}

    for path in adr_files:
        parsed_filename = identifiers.parse_filename(path.name)
        if parsed_filename is None:
            errors.append({"code": "BAD_FILENAME", "file": path.name})
            continue

        try:
            data, _ = fm.parse(path.read_text(encoding="utf-8"))
        except fm.FrontmatterError as exc:
            errors.append({"code": "BAD_FRONTMATTER", "file": path.name, "detail": str(exc)})
            continue

        for detail in validate_frontmatter(data):
            errors.append({"code": "SCHEMA_ERROR", "file": path.name, "detail": detail})

        parsed_num = parsed_filename[0]
        expected_id = f"ADR-{parsed_num:04d}"
        if data.get("id") != expected_id:
            errors.append({
                "code": "FILENAME_ID_MISMATCH",
                "file": path.name,
                "expected_id": expected_id,
                "found_id": data.get("id"),
            })

        adr_id = data.get("id")
        if adr_id:
            if adr_id in seen_ids:
                errors.append({"code": "DUPLICATE_ADR_ID", "files": [seen_ids[adr_id], path.name]})
            else:
                seen_ids[adr_id] = path.name

        parsed_entries.append((path.name, data))

    known_ids = set(seen_ids.keys())
    for filename, data in parsed_entries:
        for related_id in data.get("related", []):
            if related_id not in known_ids:
                errors.append({"code": "BROKEN_RELATED_LINK", "file": filename, "related_id": related_id})

    return {"ok": not errors, "operation": "validate", "checked": len(adr_files), "errors": errors}
