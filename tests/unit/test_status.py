from types import SimpleNamespace

from scripts.commands import status
from scripts.core import frontmatter as fm


ACCEPTED_ADR = (
    "---\n"
    "id: ADR-0001\n"
    "title: Use Kafka\n"
    "status: proposed\n"
    "date: 2026-08-01\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths: []\n"
    "tags: []\n"
    "retrospective: false\n"
    "---\n\n"
    "# Use Kafka\n"
)

ADR_WITH_SIGNIFICANT_BODY_WHITESPACE = (
    "---\n"
    "id: ADR-0001\n"
    "title: Use Kafka\n"
    "status: proposed\n"
    "date: 2026-08-01\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths: []\n"
    "tags: []\n"
    "retrospective: false\n"
    "---\n\n"
    "    # Indented body heading\n"
    "        Preserved leading indentation.\n"
    "\n\n\n"
)


def test_valid_transition_updates_status(tmp_path):
    (tmp_path / "0001-use-kafka.md").write_text(ACCEPTED_ADR, encoding="utf-8")

    result = status.run(
        SimpleNamespace(adr_number=1, to="accepted", dir=str(tmp_path), dry_run=False)
    )

    assert result["ok"] is True
    updated = (tmp_path / "0001-use-kafka.md").read_text(encoding="utf-8")
    assert "status: accepted" in updated


def test_invalid_transition_is_rejected(tmp_path):
    (tmp_path / "0001-use-kafka.md").write_text(ACCEPTED_ADR, encoding="utf-8")

    result = status.run(
        SimpleNamespace(adr_number=1, to="superseded", dir=str(tmp_path), dry_run=False)
    )

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "INVALID_TRANSITION"


def test_missing_adr_is_reported(tmp_path):
    result = status.run(
        SimpleNamespace(adr_number=99, to="accepted", dir=str(tmp_path), dry_run=False)
    )

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "ADR_NOT_FOUND"


def test_bad_frontmatter_is_reported(tmp_path):
    (tmp_path / "0001-use-kafka.md").write_text("not frontmatter at all", encoding="utf-8")

    result = status.run(
        SimpleNamespace(adr_number=1, to="accepted", dir=str(tmp_path), dry_run=False)
    )

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "BAD_FRONTMATTER"


def test_dry_run_does_not_write(tmp_path):
    (tmp_path / "0001-use-kafka.md").write_text(ACCEPTED_ADR, encoding="utf-8")

    result = status.run(
        SimpleNamespace(adr_number=1, to="accepted", dir=str(tmp_path), dry_run=True)
    )

    assert result["ok"] is True
    assert result["dry_run"] is True
    unchanged = (tmp_path / "0001-use-kafka.md").read_text(encoding="utf-8")
    assert "status: proposed" in unchanged


def test_valid_transition_preserves_parsed_body_whitespace(tmp_path):
    target = tmp_path / "0001-use-kafka.md"
    target.write_text(ADR_WITH_SIGNIFICANT_BODY_WHITESPACE, encoding="utf-8")
    before_body = fm.parse(target.read_text(encoding="utf-8"))[1]

    result = status.run(
        SimpleNamespace(adr_number=1, to="accepted", dir=str(tmp_path), dry_run=False)
    )

    assert result["ok"] is True
    after_body = fm.parse(target.read_text(encoding="utf-8"))[1]
    assert after_body == before_body
