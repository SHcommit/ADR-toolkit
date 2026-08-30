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
