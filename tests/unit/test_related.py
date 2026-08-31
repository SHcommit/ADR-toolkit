from types import SimpleNamespace

from scripts.commands import related

ADR_WITH_PATH = (
    "---\n"
    "id: ADR-0001\n"
    "title: Use Kafka for domain events\n"
    "status: accepted\n"
    "date: 2026-08-01\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths:\n"
    "  - src/events/\n"
    "tags:\n"
    "  - architecture\n"
    "retrospective: false\n"
    "---\n\n"
    "# Use Kafka for domain events\n"
)

ADR_UNRELATED = ADR_WITH_PATH.replace("0001", "0002").replace(
    "Use Kafka for domain events", "Use Postgres"
).replace("src/events/", "src/db/").replace("architecture", "data")


def test_finds_match_by_affected_path(tmp_path):
    (tmp_path / "0001-use-kafka.md").write_text(ADR_WITH_PATH, encoding="utf-8")
    (tmp_path / "0002-use-postgres.md").write_text(ADR_UNRELATED, encoding="utf-8")

    result = related.run(SimpleNamespace(dir=str(tmp_path), paths=["src/events/"], tags=None, keyword=None))

    assert result["ok"] is True
    assert result["count"] == 1
    assert result["matches"][0]["id"] == "ADR-0001"
    assert "affected_paths overlap" in result["matches"][0]["reasons"][0]


def test_finds_match_by_tag(tmp_path):
    (tmp_path / "0002-use-postgres.md").write_text(ADR_UNRELATED, encoding="utf-8")

    result = related.run(SimpleNamespace(dir=str(tmp_path), paths=None, tags=["data"], keyword=None))

    assert result["count"] == 1
    assert result["matches"][0]["id"] == "ADR-0002"


def test_no_match_returns_empty_list(tmp_path):
    (tmp_path / "0001-use-kafka.md").write_text(ADR_WITH_PATH, encoding="utf-8")

    result = related.run(SimpleNamespace(dir=str(tmp_path), paths=["src/unrelated/"], tags=None, keyword=None))

    assert result["count"] == 0
    assert result["matches"] == []


def test_bad_frontmatter_file_is_skipped_with_warning_not_aborted(tmp_path):
    (tmp_path / "0001-use-kafka.md").write_text(ADR_WITH_PATH, encoding="utf-8")
    (tmp_path / "0002-corrupted.md").write_text("not frontmatter at all", encoding="utf-8")

    result = related.run(SimpleNamespace(dir=str(tmp_path), paths=["src/events/"], tags=None, keyword=None))

    assert result["ok"] is True
    assert result["count"] == 1
    assert result["matches"][0]["id"] == "ADR-0001"
    assert result["warnings"] == [{
        "code": "BAD_FRONTMATTER",
        "file": "0002-corrupted.md",
        "detail": "No YAML frontmatter block found",
    }]


def test_non_list_affected_paths_does_not_match_by_character(tmp_path):
    malformed = ADR_WITH_PATH.replace(
        "affected_paths:\n  - src/events/\n", "affected_paths: src/events/\n"
    )
    (tmp_path / "0001-use-kafka.md").write_text(malformed, encoding="utf-8")

    result = related.run(SimpleNamespace(dir=str(tmp_path), paths=["s"], tags=None, keyword=None))

    assert result["count"] == 0
    assert result["matches"] == []


def test_keyword_matches_when_present_only_in_body(tmp_path):
    (tmp_path / "0001-cache-policy.md").write_text(
        "---\n"
        "id: ADR-0001\n"
        "title: Cache policy\n"
        "status: accepted\n"
        "date: 2026-08-31\n"
        "decision_makers: []\n"
        "related: []\n"
        "affected_paths: []\n"
        "tags: []\n"
        "retrospective: false\n"
        "---\n\n"
        "# Cache policy\n\nWe chose Redis for the shared cache layer.\n",
        encoding="utf-8",
    )

    result = related.run(SimpleNamespace(
        dir=str(tmp_path), paths=None, tags=None, keyword="redis",
    ))

    assert result["count"] == 1
    assert result["matches"][0]["id"] == "ADR-0001"
