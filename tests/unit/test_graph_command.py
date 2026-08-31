from types import SimpleNamespace

from scripts.commands import graph


def _write_adr(adr_dir, filename, *, id_, title, related=None, supersedes=None, superseded_by=None):
    lines = [
        "---",
        f"id: {id_}",
        f"title: {title}",
        "status: accepted",
        "date: 2026-08-31",
        "decision_makers: []",
    ]
    if related:
        lines.append("related:")
        lines.extend(f"  - {value}" for value in related)
    else:
        lines.append("related: []")
    lines.append("affected_paths: []")
    lines.append("tags: []")
    lines.append("retrospective: false")
    if supersedes:
        lines.append("supersedes:")
        lines.extend(f"  - {value}" for value in supersedes)
    if superseded_by:
        lines.append(f"superseded_by: {superseded_by}")
    lines.extend(["---", "", f"# {title}", ""])
    (adr_dir / filename).write_text("\n".join(lines), encoding="utf-8")


def test_graph_command_writes_mermaid_and_svg_exports(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _write_adr(adr_dir, "0001-old.md", id_="ADR-0001", title="Old", superseded_by="ADR-0002")
    _write_adr(adr_dir, "0002-new.md", id_="ADR-0002", title="New", supersedes=["ADR-0001"])

    result = graph.run(SimpleNamespace(
        dir="docs/decisions",
        root=str(tmp_path),
        output=None,
        format="both",
    ))

    assert result["ok"] is True
    assert result["count"] == 1
    assert result["outputs"] == [
        str(adr_dir / "relationships.mmd"),
        str(adr_dir / "relationships.svg"),
    ]
    assert "ADR_0002 -->|supersedes| ADR_0001" in (
        adr_dir / "relationships.mmd"
    ).read_text(encoding="utf-8")
    assert "ADR-0002 supersedes ADR-0001" in (
        adr_dir / "relationships.svg"
    ).read_text(encoding="utf-8")


def test_graph_command_can_write_only_mermaid_to_custom_output(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _write_adr(adr_dir, "0001-a.md", id_="ADR-0001", title="A", related=["ADR-0002"])
    _write_adr(adr_dir, "0002-b.md", id_="ADR-0002", title="B")
    output = tmp_path / "graph.mmd"

    result = graph.run(SimpleNamespace(
        dir=str(adr_dir),
        root=str(tmp_path),
        output=str(output),
        format="mermaid",
    ))

    assert result["ok"] is True
    assert result["outputs"] == [str(output)]
    assert "ADR_0001 -.->|related| ADR_0002" in output.read_text(encoding="utf-8")


def test_graph_command_uses_custom_output_as_prefix_for_both_formats(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _write_adr(adr_dir, "0001-a.md", id_="ADR-0001", title="A", related=["ADR-0002"])
    _write_adr(adr_dir, "0002-b.md", id_="ADR-0002", title="B")

    result = graph.run(SimpleNamespace(
        dir="docs/decisions",
        root=str(tmp_path),
        output="build/adr-relationships",
        format="both",
    ))

    assert result["ok"] is True
    assert result["outputs"] == [
        str(tmp_path / "build" / "adr-relationships.mmd"),
        str(tmp_path / "build" / "adr-relationships.svg"),
    ]
    assert (tmp_path / "build" / "adr-relationships.mmd").is_file()
    assert (tmp_path / "build" / "adr-relationships.svg").is_file()


def test_graph_command_resolves_relative_single_output_against_root(tmp_path, monkeypatch):
    caller = tmp_path / "caller"
    repo = tmp_path / "repo"
    adr_dir = repo / "docs" / "decisions"
    caller.mkdir()
    adr_dir.mkdir(parents=True)
    _write_adr(adr_dir, "0001-a.md", id_="ADR-0001", title="A", related=["ADR-0002"])
    _write_adr(adr_dir, "0002-b.md", id_="ADR-0002", title="B")
    monkeypatch.chdir(caller)

    result = graph.run(SimpleNamespace(
        dir="docs/decisions",
        root=str(repo),
        output="docs/decisions/custom.svg",
        format="svg",
    ))

    assert result["ok"] is True
    assert result["outputs"] == [str(repo / "docs" / "decisions" / "custom.svg")]
    assert (repo / "docs" / "decisions" / "custom.svg").is_file()
    assert not (caller / "docs" / "decisions" / "custom.svg").exists()
