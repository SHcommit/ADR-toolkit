"""Canonical ADR relationship model, shared by index.py and validate.py."""
from html import escape
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


def render_mermaid(entries: list) -> str:
    """Render ADR relationships as GitHub-compatible Mermaid flowchart text."""
    by_id = _entries_by_id(entries)
    relationships = resolve(entries)
    visual_edges = _visual_edges(relationships)
    lines = ["flowchart LR"]

    for adr_id in sorted(by_id):
        entry = by_id[adr_id]
        label = _mermaid_label(adr_id, entry.get("title", adr_id))
        lines.append(f"  {_node_id(adr_id)}[\"{label}\"]")

    if not visual_edges:
        lines.append('  EMPTY["No relationships recorded"]')

    for relationship in sorted(visual_edges):
        source = _node_id(relationship.source)
        target = _node_id(relationship.target)
        if relationship.type == "related":
            lines.append(f"  {source} -.->|related| {target}")
        else:
            lines.append(f"  {source} -->|supersedes| {target}")

    return "\n".join(lines) + "\n"


def render_svg(entries: list) -> str:
    """Render a small deterministic SVG navigation artifact.

    This is intentionally not a full Mermaid renderer. It uses the same graph
    model and writes vector text/lines directly so the exported artifact stays
    sharp without requiring Node or browser automation.
    """
    by_id = _entries_by_id(entries)
    relationships = _visual_edges(resolve(entries))
    ordered_ids = sorted(by_id)
    width = 960
    row_height = 82
    edge_height = 28
    node_height = max(1, len(ordered_ids)) * row_height
    edge_start = 72 + node_height
    height = edge_start + max(1, len(relationships)) * edge_height + 48
    y_by_id = {adr_id: 72 + index * row_height for index, adr_id in enumerate(ordered_ids)}

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        "<title>ADR relationship graph</title>",
        "<desc>Vector export of ADR supersession and related-decision links.</desc>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#52616f"/></marker></defs>',
        '<text x="32" y="34" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="#1f2933">ADR relationship graph</text>',
    ]

    for adr_id in ordered_ids:
        y = y_by_id[adr_id]
        title = str(by_id[adr_id].get("title", adr_id))
        lines.extend([
            f'<rect x="32" y="{y}" width="292" height="52" rx="6" fill="#f8fafc" stroke="#9fb3c8"/>',
            f'<text x="48" y="{y + 22}" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="#102a43">{escape(adr_id)}</text>',
            f'<text x="48" y="{y + 42}" font-family="Arial, sans-serif" font-size="13" fill="#334e68">{escape(_truncate(title, 36))}</text>',
        ])

    if relationships:
        pair_totals = {}
        for relationship in relationships:
            pair = (relationship.source, relationship.target)
            pair_totals[pair] = pair_totals.get(pair, 0) + 1
        pair_seen = {}
        for index, relationship in enumerate(sorted(relationships)):
            pair = (relationship.source, relationship.target)
            pair_seen[pair] = pair_seen.get(pair, 0) + 1
            offset = (pair_seen[pair] - (pair_totals[pair] + 1) / 2) * 14
            source_y = y_by_id.get(relationship.source, 72) + 26 + offset
            target_y = y_by_id.get(relationship.target, 72) + 26 + offset
            edge_y = edge_start + index * edge_height
            label = f"{relationship.source} {relationship.type} {relationship.target}"
            dash = ' stroke-dasharray="5 5"' if relationship.type == "related" else ""
            lines.extend([
                f'<path d="M 324 {source_y} C 520 {source_y}, 520 {target_y}, 324 {target_y}" fill="none" stroke="#52616f" stroke-width="1.8"{dash} marker-end="url(#arrow)"/>',
                f'<text x="640" y="{edge_y}" font-family="Arial, sans-serif" font-size="13" fill="#334e68">{escape(label)}</text>',
            ])
    else:
        lines.append('<text x="32" y="132" font-family="Arial, sans-serif" font-size="14" fill="#52616f">No relationships recorded</text>')

    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _entries_by_id(entries: list) -> dict:
    return {entry["id"]: entry for entry in entries if entry.get("id")}


def _visual_edges(relationships: list) -> list:
    return [r for r in relationships if r.type in {"related", "supersedes"}]


def _node_id(adr_id: str) -> str:
    return adr_id.replace("-", "_")


def _mermaid_label(adr_id: str, title: str) -> str:
    safe_title = " ".join(str(title).split())
    safe_title = escape(safe_title, quote=False)
    safe_title = safe_title.replace('"', "'").replace("[", "(").replace("]", ")")
    return f"{adr_id}<br/>{safe_title}"


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."
