from scripts.core.relationships import Relationship, resolve

ENTRIES = [
    {"id": "ADR-0003", "related": [], "supersedes": [], "superseded_by": "ADR-0006"},
    {"id": "ADR-0006", "related": [], "supersedes": ["ADR-0003"], "superseded_by": None},
    {"id": "ADR-0007", "related": ["ADR-0002"], "supersedes": [], "superseded_by": None},
    {"id": "ADR-0002", "related": [], "supersedes": [], "superseded_by": None},
]


def test_resolve_produces_supersedes_edge():
    edges = resolve(ENTRIES)
    assert Relationship(source="ADR-0006", type="supersedes", target="ADR-0003") in edges


def test_resolve_produces_superseded_by_edge():
    edges = resolve(ENTRIES)
    assert Relationship(source="ADR-0003", type="superseded_by", target="ADR-0006") in edges


def test_resolve_produces_related_edge():
    edges = resolve(ENTRIES)
    assert Relationship(source="ADR-0007", type="related", target="ADR-0002") in edges


def test_resolve_produces_no_edges_for_entry_with_no_relationships():
    edges = resolve(ENTRIES)
    assert not any(e.source == "ADR-0002" for e in edges)


def test_resolve_handles_missing_fields_gracefully():
    edges = resolve([{"id": "ADR-0001"}])
    assert edges == []
