"""General ADR lookup: keyword (title+body), tags, status, or governed path.

Distinct from related.py's discovery policy (broad OR, no-query-means-no-
match): search.py combines different filter fields with AND, multiple values
within one field with OR, and an empty query browses every ADR.
"""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core.adr_directory import iter_adr_files
from scripts.core.query import matches_tags_any, path_governed_by, rank_key


def run(args) -> dict:
    adr_dir = Path(args.dir)
    keyword = (getattr(args, "keyword", None) or "").lower()
    query_tags = set(getattr(args, "tags", None) or [])
    status = getattr(args, "status", None)
    path = getattr(args, "path", None)
    limit = getattr(args, "limit", None)

    results = []
    warnings = []
    for entry, parsed in iter_adr_files(adr_dir):
        if parsed is None:
            continue

        try:
            data, body = fm.parse(entry.read_text(encoding="utf-8"))
        except fm.FrontmatterError as exc:
            warnings.append({"code": "BAD_FRONTMATTER", "file": entry.name, "detail": str(exc)})
            continue

        matched_in = []

        if keyword:
            title_hit = keyword in (data.get("title") or "").lower()
            body_hit = keyword in (body or "").lower()
            if not (title_hit or body_hit):
                continue
            if title_hit:
                matched_in.append("title")
            if body_hit:
                matched_in.append("body")

        if query_tags:
            tag_overlap = matches_tags_any(query_tags, data.get("tags"))
            if not tag_overlap:
                continue
            matched_in.append("tags")

        if status:
            if data.get("status") != status:
                continue
            matched_in.append("status")

        if path:
            if not path_governed_by(path, data.get("affected_paths")):
                continue
            matched_in.append("path")

        results.append({
            "id": data.get("id"),
            "filename": entry.name,
            "path": str(Path(args.dir) / entry.name),
            "title": data.get("title"),
            "status": data.get("status"),
            "tags": data.get("tags", []),
            "matched_in": matched_in,
            "_body": body,  # used only for ranking below, stripped before returning
        })

    results.sort(key=lambda r: rank_key({"id": r["id"], "title": r["title"], "body": r["_body"]}, keyword))
    for r in results:
        del r["_body"]

    total = len(results)
    if limit is not None:
        truncated = total > limit
        results = results[:limit]
    else:
        truncated = False

    return {
        "ok": True,
        "operation": "search",
        "query": {
            "keyword": getattr(args, "keyword", None),
            "tags": getattr(args, "tags", None),
            "status": status,
            "path": path,
            "limit": limit,
        },
        "count": len(results),
        "total": total,
        "truncated": truncated,
        "results": results,
        "warnings": warnings,
    }
