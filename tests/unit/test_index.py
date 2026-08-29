from types import SimpleNamespace

from scripts.commands import index


def _write_adr(adr_dir, filename, *, id_, title, status, date, tags, affected_paths):
    tags_block = "\n".join(f"  - {t}" for t in tags) or None
    paths_block = "\n".join(f"  - {p}" for p in affected_paths) or None
    text = (
        "---\n"
        f"id: {id_}\n"
        f"title: {title}\n"
        f"status: {status}\n"
        f"date: {date}\n"
        "decision_makers: []\n"
        "related: []\n"
        f"affected_paths:\n{paths_block}\n"
        f"tags:\n{tags_block}\n"
        "retrospective: false\n"
        "---\n\n"
        f"# {title}\n"
    )
    (adr_dir / filename).write_text(text, encoding="utf-8")


def test_index_generates_readme_with_all_views(tmp_path):
    adr_dir = tmp_path
    _write_adr(
        adr_dir, "0001-use-kafka.md",
        id_="ADR-0001", title="Use Kafka", status="accepted", date="2026-08-01",
        tags=["architecture"], affected_paths=["src/events/"],
    )
    _write_adr(
        adr_dir, "0002-use-postgres.md",
        id_="ADR-0002", title="Use Postgres", status="proposed", date="2026-08-15",
        tags=["architecture", "data"], affected_paths=["src/db/"],
    )

    result = index.run(SimpleNamespace(dir=str(adr_dir)))

    assert result["ok"] is True
    assert result["count"] == 2
    readme = (adr_dir / "README.md").read_text(encoding="utf-8")
    assert "## By status" in readme
    assert "## By tag" in readme
    assert "## By affected path" in readme
    assert "## Chronological" in readme
    assert "ADR-0001" in readme and "ADR-0002" in readme
    assert "`src/events/`" in readme


def test_index_skips_readme_and_template_files(tmp_path):
    (tmp_path / "adr-template.md").write_text("not an ADR", encoding="utf-8")
    result = index.run(SimpleNamespace(dir=str(tmp_path)))
    assert result["count"] == 0


def test_index_skips_malformed_frontmatter_file_with_warning_instead_of_raising(tmp_path):
    (tmp_path / "0001-malformed.md").write_text("not frontmatter at all\n", encoding="utf-8")

    result = index.run(SimpleNamespace(dir=str(tmp_path)))

    assert result["ok"] is True
    assert result["count"] == 0
    assert any(w["code"] == "BAD_FRONTMATTER" and w["file"] == "0001-malformed.md" for w in result["warnings"])
