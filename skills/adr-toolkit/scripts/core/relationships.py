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


def find_cycles(relationships: list) -> list:
    """Detect cycles among "supersedes" edges only -- "related" is symmetric
    in meaning, so an A<->B related pair is not a logical error the way a
    supersession cycle (A supersedes B supersedes A) is.

    Returns a list of cycle paths, each a tuple of ADR ids in the order the
    depth-first walk encountered them.
    """
    graph: dict = {}
    for r in relationships:
        if r.type == "supersedes":
            graph.setdefault(r.source, []).append(r.target)

    cycles = []
    visited = set()

    def dfs(node, path, path_set):
        if node in path_set:
            cycle_start = path.index(node)
            cycle = tuple(path[cycle_start:])
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if node in visited:
            return
        visited.add(node)
        path.append(node)
        path_set.add(node)
        for neighbor in graph.get(node, []):
            dfs(neighbor, path, path_set)
        path.pop()
        path_set.discard(node)

    for node in sorted(graph):
        dfs(node, [], set())

    return cycles
