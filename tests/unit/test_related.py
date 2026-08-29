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
