"""Find existing ADRs related to a set of paths, tags, or a keyword."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers

SKIP_FILES = {"README.md", "adr-template.md"}


def run(args) -> dict:
    adr_dir = Path(args.dir)
    query_paths = set(getattr(args, "paths", None) or [])
    query_tags = set(getattr(args, "tags", None) or [])
    keyword = (getattr(args, "keyword", None) or "").lower()

    matches = []
    for entry in sorted(adr_dir.glob("*.md")):
        if entry.name in SKIP_FILES or identifiers.parse_filename(entry.name) is None:
            continue

        data, _ = fm.parse(entry.read_text(encoding="utf-8"))
        reasons = []

        path_overlap = query_paths & set(data.get("affected_paths", []))
        if path_overlap:
            reasons.append(f"affected_paths overlap: {sorted(path_overlap)}")

        tag_overlap = query_tags & set(data.get("tags", []))
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

    return {"ok": True, "operation": "related", "count": len(matches), "matches": matches}
