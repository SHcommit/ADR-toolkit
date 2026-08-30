"""Shared ADR matching primitives for related.py and search.py.

related.py wants a broad net (any single field overlap is enough); search.py
wants precise filtering (all given fields must match). Both call the same
functions here; the combination policy lives in each command, not here.
"""
from scripts.core import globs


def matches_keyword(keyword: str, title: str, body: str) -> bool:
    keyword = keyword.lower()
    return keyword in (title or "").lower() or keyword in (body or "").lower()


def matches_tags_any(query_tags: set, entry_tags: list) -> set:
    return query_tags & set(entry_tags or [])


def matches_paths_exact(query_paths: set, affected_paths: list) -> set:
    return query_paths & set(affected_paths or [])


def path_governed_by(path: str, affected_paths: list) -> bool:
    return any(
        globs.path_under(path, ap) or globs.match(ap, path)
        for ap in (affected_paths or [])
        if isinstance(ap, str)
    )


def rank_key(entry: dict, keyword: str) -> tuple:
    """Lower tuples sort first -- tier 0 (best) through tier 4 (worst), then
    id as a stable, deterministic tie-break."""
    keyword_lower = (keyword or "").lower()
    title_lower = (entry.get("title") or "").lower()
    body_lower = (entry.get("body") or "").lower()

    if keyword_lower and entry.get("id", "").lower() == keyword_lower:
        tier = 0
    elif keyword_lower and title_lower == keyword_lower:
        tier = 1
    elif keyword_lower and keyword_lower in title_lower:
        tier = 2
    elif keyword_lower and keyword_lower in body_lower:
        tier = 4
    else:
        tier = 3  # tag-only or no-keyword matches land between title and body
    return (tier, entry.get("id", ""))
