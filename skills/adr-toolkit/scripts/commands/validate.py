"""Validate ADR directory structural integrity: IDs, frontmatter, and links."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core.adr_directory import iter_adr_files
from scripts.core.config import ConfigError, load_repository_config
from scripts.core.relationships import find_cycles, missing_targets, resolve, supersession_mismatches
from scripts.core.schema import validate_frontmatter
from scripts.core.repository_paths import resolve_from_root_or_error


def run(args) -> dict:
    root = Path(getattr(args, "root", "."))
    adr_dir, error = resolve_from_root_or_error(root, args.dir, operation="validate")
    if error:
        return error
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

    parsed_entries = []
    seen_ids: dict = {}
    checked = 0

    for path, parsed_filename in iter_adr_files(adr_dir):
        checked += 1
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

    edges = resolve([data for _, data in parsed_entries])

    for edge in missing_targets(edges, known_ids):
        if edge.type in ("supersedes", "superseded_by"):
            errors.append({
                "code": "BROKEN_SUPERSESSION_LINK",
                "adr_id": edge.source,
                "target": edge.target,
            })

    for source, target in supersession_mismatches(edges):
        errors.append({
            "code": "SUPERSESSION_MISMATCH",
            "adr_id": source,
            "expected_superseded_by_on": target,
        })

    for cycle in find_cycles(edges):
        errors.append({"code": "SUPERSESSION_CYCLE", "cycle": list(cycle)})

    return {"ok": not errors, "operation": "validate", "checked": checked, "errors": errors}
