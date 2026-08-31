from scripts.core.relationships import (
    Relationship,
    find_cycles,
    missing_targets,
    render_mermaid,
    render_svg,
    resolve,
    supersession_mismatches,
)

ENTRIES = [
    {"id": "ADR-0003", "title": "Old decision", "related": [], "supersedes": [], "superseded_by": "ADR-0006"},
    {"id": "ADR-0006", "title": "New decision", "related": [], "supersedes": ["ADR-0003"], "superseded_by": None},
    {"id": "ADR-0007", "title": "Confidence field", "related": ["ADR-0002"], "supersedes": [], "superseded_by": None},
    {"id": "ADR-0002", "title": "Structural checks", "related": [], "supersedes": [], "superseded_by": None},
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


def test_missing_targets_finds_dangling_reference():
    edges = resolve([{"id": "ADR-0001", "related": ["ADR-9999"]}])
    missing = missing_targets(edges, known_ids={"ADR-0001"})
    assert Relationship(source="ADR-0001", type="related", target="ADR-9999") in missing


def test_missing_targets_empty_when_all_targets_known():
    edges = resolve(ENTRIES)
    known_ids = {e["id"] for e in ENTRIES}
    assert missing_targets(edges, known_ids) == []


def test_supersession_mismatches_empty_when_bidirectional():
    edges = resolve(ENTRIES)
    assert supersession_mismatches(edges) == []


def test_supersession_mismatches_finds_one_sided_edge():
    one_sided = [
        {"id": "ADR-0010", "related": [], "supersedes": ["ADR-0009"], "superseded_by": None},
        {"id": "ADR-0009", "related": [], "supersedes": [], "superseded_by": None},
    ]
    edges = resolve(one_sided)
    mismatches = supersession_mismatches(edges)
    assert ("ADR-0010", "ADR-0009") in mismatches


def test_find_cycles_empty_for_a_linear_chain():
    linear = [
        {"id": "ADR-0001", "supersedes": [], "superseded_by": "ADR-0002"},
        {"id": "ADR-0002", "supersedes": ["ADR-0001"], "superseded_by": None},
    ]
    assert find_cycles(resolve(linear)) == []


def test_find_cycles_detects_a_direct_two_node_cycle():
    mutual = [
        {"id": "ADR-0001", "supersedes": ["ADR-0002"], "superseded_by": None},
        {"id": "ADR-0002", "supersedes": ["ADR-0001"], "superseded_by": None},
    ]
    cycles = find_cycles(resolve(mutual))
    assert len(cycles) == 1
    assert set(cycles[0]) == {"ADR-0001", "ADR-0002"}


def test_find_cycles_detects_a_longer_cycle():
    triangle = [
        {"id": "ADR-0001", "supersedes": ["ADR-0002"], "superseded_by": None},
        {"id": "ADR-0002", "supersedes": ["ADR-0003"], "superseded_by": None},
        {"id": "ADR-0003", "supersedes": ["ADR-0001"], "superseded_by": None},
    ]
    cycles = find_cycles(resolve(triangle))
    assert len(cycles) == 1
    assert set(cycles[0]) == {"ADR-0001", "ADR-0002", "ADR-0003"}


def test_find_cycles_ignores_related_edges():
    # related is symmetric/non-directional in meaning; A<->B related is not
    # a logical error the way a supersession cycle is.
    mutually_related = [
        {"id": "ADR-0001", "related": ["ADR-0002"]},
        {"id": "ADR-0002", "related": ["ADR-0001"]},
    ]
    assert find_cycles(resolve(mutually_related)) == []


def test_render_mermaid_includes_supersession_and_related_edges_with_labels():
    mermaid = render_mermaid(ENTRIES)

    assert mermaid.startswith("flowchart LR\n")
    assert "ADR_0006[\"ADR-0006<br/>New decision\"]" in mermaid
    assert "ADR_0006 -->|supersedes| ADR_0003" in mermaid
    assert "ADR_0007 -.->|related| ADR_0002" in mermaid
    assert "ADR_0003 -->|superseded by| ADR_0006" not in mermaid


def test_render_mermaid_reports_no_relationships_when_graph_has_no_edges():
    mermaid = render_mermaid([{"id": "ADR-0001", "title": "Lonely decision"}])

    assert "ADR_0001[\"ADR-0001<br/>Lonely decision\"]" in mermaid
    assert "No relationships recorded" in mermaid


def test_render_mermaid_escapes_title_text_for_label_safety():
    mermaid = render_mermaid([
        {"id": "ADR-0001", "title": "Use <A&B> \"ports\" [core]\nnow"},
    ])

    assert "Use &lt;A&amp;B&gt; 'ports' (core) now" in mermaid
    assert "\nnow" not in mermaid


def test_render_svg_returns_crisp_vector_navigation_artifact():
    svg = render_svg(ENTRIES)

    assert svg.startswith("<svg ")
    assert "<title>ADR relationship graph</title>" in svg
    assert "ADR-0006" in svg and "New decision" in svg
    assert "ADR-0006 supersedes ADR-0003" in svg
    assert "ADR-0007 related ADR-0002" in svg
