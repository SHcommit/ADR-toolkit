from types import SimpleNamespace

from scripts.commands import search


def _yaml_list_field(key, values):
    if not values:
        return f"{key}: []"
    return f"{key}:\n" + "\n".join(f"  - {v}" for v in values)


def _write_adr(adr_dir, filename, id, title, status="accepted", affected_paths=None, tags=None, body="Body text."):
    adr_dir.mkdir(parents=True, exist_ok=True)
    text = (
        "---\n"
        f"id: {id}\n"
        f"title: {title}\n"
        f"status: {status}\n"
        "date: 2026-08-31\n"
        "decision_makers: []\n"
        "related: []\n"
        f"{_yaml_list_field('affected_paths', affected_paths)}\n"
        f"{_yaml_list_field('tags', tags)}\n"
        "retrospective: false\n"
        "---\n\n"
        f"# {title}\n\n"
        f"{body}\n"
    )
    (adr_dir / filename).write_text(text, encoding="utf-8")


def _args(adr_dir, **overrides):
    defaults = dict(dir=str(adr_dir), keyword=None, tags=None, status=None, path=None, limit=None)
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_search_with_no_filters_returns_every_adr(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    _write_adr(adr_dir, "0001-a.md", id="ADR-0001", title="First")
    _write_adr(adr_dir, "0002-b.md", id="ADR-0002", title="Second")

    result = search.run(_args(adr_dir))

    assert result["count"] == 2


def test_search_keyword_matches_title(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    _write_adr(adr_dir, "0001-a.md", id="ADR-0001", title="Cache policy")
    _write_adr(adr_dir, "0002-b.md", id="ADR-0002", title="Unrelated")

    result = search.run(_args(adr_dir, keyword="cache"))

    assert result["count"] == 1
    assert result["results"][0]["id"] == "ADR-0001"


def test_search_keyword_matches_body(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    _write_adr(adr_dir, "0001-a.md", id="ADR-0001", title="Cache policy", body="We chose Redis.")

    result = search.run(_args(adr_dir, keyword="redis"))

    assert result["count"] == 1


def test_search_tag_filter(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    _write_adr(adr_dir, "0001-a.md", id="ADR-0001", title="A", tags=["database"])
    _write_adr(adr_dir, "0002-b.md", id="ADR-0002", title="B", tags=["cli"])

    result = search.run(_args(adr_dir, tags=["database"]))

    assert result["count"] == 1
    assert result["results"][0]["id"] == "ADR-0001"


def test_search_status_filter(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    _write_adr(adr_dir, "0001-a.md", id="ADR-0001", title="A", status="accepted")
    _write_adr(adr_dir, "0002-b.md", id="ADR-0002", title="B", status="proposed")

    result = search.run(_args(adr_dir, status="proposed"))

    assert result["count"] == 1
    assert result["results"][0]["id"] == "ADR-0002"


def test_search_path_filter_uses_governed_by_semantics(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    _write_adr(adr_dir, "0001-a.md", id="ADR-0001", title="A", affected_paths=["src/db/"])
    _write_adr(adr_dir, "0002-b.md", id="ADR-0002", title="B", affected_paths=["src/api/"])

    result = search.run(_args(adr_dir, path="src/db/connection.py"))

    assert result["count"] == 1
    assert result["results"][0]["id"] == "ADR-0001"


def test_search_combines_different_fields_with_and(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    _write_adr(adr_dir, "0001-a.md", id="ADR-0001", title="Cache policy", tags=["database"])
    _write_adr(adr_dir, "0002-b.md", id="ADR-0002", title="Cache policy", tags=["cli"])

    result = search.run(_args(adr_dir, keyword="cache", tags=["database"]))

    assert result["count"] == 1
    assert result["results"][0]["id"] == "ADR-0001"


def test_search_combines_same_field_values_with_or(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    _write_adr(adr_dir, "0001-a.md", id="ADR-0001", title="A", tags=["postgres"])
    _write_adr(adr_dir, "0002-b.md", id="ADR-0002", title="B", tags=["mysql"])
    _write_adr(adr_dir, "0003-c.md", id="ADR-0003", title="C", tags=["cli"])

    result = search.run(_args(adr_dir, tags=["postgres", "mysql"]))

    assert result["count"] == 2


def test_search_orders_exact_title_match_before_substring_match(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    _write_adr(adr_dir, "0001-a.md", id="ADR-0001", title="cache policy extended")
    _write_adr(adr_dir, "0002-b.md", id="ADR-0002", title="cache")

    result = search.run(_args(adr_dir, keyword="cache"))

    assert [r["id"] for r in result["results"]] == ["ADR-0002", "ADR-0001"]


def test_search_limit_truncates_and_reports_total(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    _write_adr(adr_dir, "0001-a.md", id="ADR-0001", title="A")
    _write_adr(adr_dir, "0002-b.md", id="ADR-0002", title="B")
    _write_adr(adr_dir, "0003-c.md", id="ADR-0003", title="C")

    result = search.run(_args(adr_dir, limit=2))

    assert result["count"] == 2
    assert result["total"] == 3
    assert result["truncated"] is True
    assert len(result["results"]) == 2


def test_search_no_limit_is_not_truncated(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    _write_adr(adr_dir, "0001-a.md", id="ADR-0001", title="A")

    result = search.run(_args(adr_dir))

    assert result["total"] == 1
    assert result["truncated"] is False


def test_search_echoes_the_query(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    _write_adr(adr_dir, "0001-a.md", id="ADR-0001", title="A", tags=["cli"])

    result = search.run(_args(adr_dir, keyword="a", tags=["cli"], status="accepted"))

    assert result["query"] == {
        "keyword": "a", "tags": ["cli"], "status": "accepted", "path": None, "limit": None,
    }


def test_search_malformed_adr_degrades_to_warning(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-bad.md").write_text("not valid frontmatter", encoding="utf-8")

    result = search.run(_args(adr_dir))

    assert result["ok"] is True
    assert result["count"] == 0
    assert any(w["code"] == "BAD_FRONTMATTER" for w in result["warnings"])
