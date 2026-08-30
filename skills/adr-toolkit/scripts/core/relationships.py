"""Canonical ADR relationship model, shared by index.py and validate.py."""
from typing import NamedTuple


class Relationship(NamedTuple):
    source: str
    type: str  # "related" | "supersedes" | "superseded_by"
    target: str


def resolve(entries: list) -> list:
    edges = []
    for entry in entries:
        source = entry.get("id")
        for target in entry.get("related") or []:
            edges.append(Relationship(source=source, type="related", target=target))
        for target in entry.get("supersedes") or []:
            edges.append(Relationship(source=source, type="supersedes", target=target))
        superseded_by = entry.get("superseded_by")
        if superseded_by:
            edges.append(Relationship(source=source, type="superseded_by", target=superseded_by))
    return edges


def missing_targets(relationships: list, known_ids: set) -> list:
    return [r for r in relationships if r.target not in known_ids]


def supersession_mismatches(relationships: list) -> list:
    supersedes_edges = {(r.source, r.target) for r in relationships if r.type == "supersedes"}
    superseded_by_edges = {(r.target, r.source) for r in relationships if r.type == "superseded_by"}
    return sorted(supersedes_edges - superseded_by_edges)
