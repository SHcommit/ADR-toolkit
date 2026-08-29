from types import SimpleNamespace

from scripts.commands import status


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


def test_dry_run_does_not_write(tmp_path):
    (tmp_path / "0001-use-kafka.md").write_text(ACCEPTED_ADR, encoding="utf-8")

    result = status.run(
        SimpleNamespace(adr_number=1, to="accepted", dir=str(tmp_path), dry_run=True)
    )

    assert result["ok"] is True
    assert result["dry_run"] is True
    unchanged = (tmp_path / "0001-use-kafka.md").read_text(encoding="utf-8")
    assert "status: proposed" in unchanged
