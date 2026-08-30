"""Find existing ADRs related to a set of paths, tags, or a keyword."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core.adr_directory import iter_adr_files


def _as_list(value) -> list:
    return value if isinstance(value, list) else []


def run(args) -> dict:
    adr_dir = Path(args.dir)
    query_paths = set(getattr(args, "paths", None) or [])
    query_tags = set(getattr(args, "tags", None) or [])
    keyword = (getattr(args, "keyword", None) or "").lower()

    matches = []
    warnings = []
    for entry, parsed in iter_adr_files(adr_dir):
        if parsed is None:
            continue

        try:
            data, _ = fm.parse(entry.read_text(encoding="utf-8"))
        except fm.FrontmatterError as exc:
            warnings.append({"code": "BAD_FRONTMATTER", "file": entry.name, "detail": str(exc)})
            continue

        reasons = []

        path_overlap = query_paths & set(_as_list(data.get("affected_paths")))
        if path_overlap:
            reasons.append(f"affected_paths overlap: {sorted(path_overlap)}")

        tag_overlap = query_tags & set(_as_list(data.get("tags")))
        if tag_overlap:
            reasons.append(f"tag overlap: {sorted(tag_overlap)}")

        if keyword and keyword in data.get("title", "").lower():
            reasons.append("title keyword match")

        if reasons:
            matches.append({
                "id": data.get("id"),
                "filename": entry.name,
                "title": data.get("title"),
                "status": data.get("status"),
                "reasons": reasons,
            })

    return {
        "ok": True,
        "operation": "related",
        "count": len(matches),
        "matches": matches,
        "warnings": warnings,
    }
