from types import SimpleNamespace

from scripts.commands import index


def _write_adr(adr_dir, filename, *, id_, title, status, date, tags, affected_paths):
    if affected_paths:
        paths_field = "affected_paths:\n" + "\n".join(f"  - {p}" for p in affected_paths)
    else:
        paths_field = "affected_paths: []"
    if tags:
        tags_field = "tags:\n" + "\n".join(f"  - {t}" for t in tags)
    else:
        tags_field = "tags: []"
    text = (
        "---\n"
        f"id: {id_}\n"
        f"title: {title}\n"
        f"status: {status}\n"
        f"date: {date}\n"
        "decision_makers: []\n"
        "related: []\n"
        f"{paths_field}\n"
        f"{tags_field}\n"
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


def test_index_renders_french_headers_and_status_labels(tmp_path):
    _write_adr(
        tmp_path, "0001-use-kafka.md",
        id_="ADR-0001", title="Use Kafka", status="accepted", date="2026-08-01",
        tags=["architecture"], affected_paths=["src/events/"],
    )

    result = index.run(SimpleNamespace(dir=str(tmp_path), locale="fr"))

    assert result["ok"] is True
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "Journal des décisions" in readme
    assert "Par statut" in readme
    assert "Accepté" in readme
    assert "Par étiquette" in readme
    assert "Par chemin concerné" in readme
    assert "Chronologique (plus récent d'abord)" in readme


def test_index_defaults_to_english_when_locale_omitted(tmp_path):
    _write_adr(
        tmp_path, "0001-use-kafka.md",
        id_="ADR-0001", title="Use Kafka", status="accepted", date="2026-08-01",
        tags=["architecture"], affected_paths=["src/events/"],
    )

    result = index.run(SimpleNamespace(dir=str(tmp_path), root=str(tmp_path), locale=None))

    assert result["ok"] is True
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "# Decision Log" in readme
    assert "## By status" in readme


def test_index_uses_repository_default_when_locale_omitted(tmp_path):
    (tmp_path / ".adr-toolkit.json").write_text(
        '{"schema_version": 1, "locale": "ko"}', encoding="utf-8"
    )
    adr_dir = tmp_path / "docs/decisions"
    adr_dir.mkdir(parents=True)

    result = index.run(SimpleNamespace(
        dir=str(adr_dir), root=str(tmp_path), locale=None,
    ))

    assert result["ok"] is True
    assert (adr_dir / "README.md").read_text(encoding="utf-8").startswith("# 결정 기록")


def test_relative_adr_directory_is_resolved_against_root(tmp_path, monkeypatch):
    caller = tmp_path / "caller"
    repo = tmp_path / "repo"
    adr_dir = repo / "docs/decisions"
    caller.mkdir()
    adr_dir.mkdir(parents=True)
    monkeypatch.chdir(caller)

    result = index.run(SimpleNamespace(
        dir="docs/decisions", root=str(repo), locale="en",
    ))

    assert result["ok"] is True
    assert (adr_dir / "README.md").is_file()
    assert not (caller / "docs/decisions/README.md").exists()


def test_index_unknown_status_falls_back_to_capitalized_label(tmp_path):
    _write_adr(
        tmp_path, "0001-use-kafka.md",
        id_="ADR-0001", title="Use Kafka", status="unknown", date="2026-08-01",
        tags=[], affected_paths=[],
    )

    result = index.run(SimpleNamespace(dir=str(tmp_path), locale="fr"))

    assert result["ok"] is True
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "### Unknown" in readme


def test_index_survives_a_malformed_locale_file(tmp_path, monkeypatch):
    """Design spec 17.1: a bad locale file degrades, never crashes."""
    import scripts.core.locale as locale_module
    broken_dir = tmp_path / "i18n"
    broken_dir.mkdir()
    (broken_dir / "en.json").write_text(
        '{"decision_log_title": "Decision Log", "by_status": "By status",'
        ' "by_tag": "By tag", "by_affected_path": "By affected path",'
        ' "chronological": "Chronological (newest first)"}',
        encoding="utf-8",
    )
    (broken_dir / "fr.json").write_text("not json at all", encoding="utf-8")
    monkeypatch.setattr(locale_module, "I18N_DIR", broken_dir)

    adr_dir = tmp_path / "decisions"
    adr_dir.mkdir()
    _write_adr(
        adr_dir, "0001-use-kafka.md",
        id_="ADR-0001", title="Use Kafka", status="accepted", date="2026-08-01",
        tags=["architecture"], affected_paths=["src/events/"],
    )

    result = index.run(SimpleNamespace(dir=str(adr_dir), locale="fr"))

    assert result["ok"] is True
    readme = (adr_dir / "README.md").read_text(encoding="utf-8")
    assert "# Decision Log" in readme
    assert "## By status" in readme


def test_index_survives_a_completely_absent_i18n_directory(tmp_path, monkeypatch):
    """A copy-based install that omitted scripts/i18n/ still produces English."""
    import scripts.core.locale as locale_module
    monkeypatch.setattr(locale_module, "I18N_DIR", tmp_path / "no-such-i18n")

    adr_dir = tmp_path / "decisions"
    adr_dir.mkdir()
    _write_adr(
        adr_dir, "0001-use-kafka.md",
        id_="ADR-0001", title="Use Kafka", status="accepted", date="2026-08-01",
        tags=["architecture"], affected_paths=["src/events/"],
    )

    result = index.run(SimpleNamespace(dir=str(adr_dir), locale="fr"))

    assert result["ok"] is True
    readme = (adr_dir / "README.md").read_text(encoding="utf-8")
    assert "# Decision Log" in readme
    assert "## By status" in readme
    assert "## By tag" in readme
    assert "## By affected path" in readme
    assert "## Chronological (newest first)" in readme
    assert "### Accepted" in readme
    assert "ADR-0001" in readme
