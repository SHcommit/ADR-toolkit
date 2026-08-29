from types import SimpleNamespace

import pytest

from scripts.commands import supersede
from scripts.core import frontmatter as fm


OLD_ADR = (
    "---\n"
    "id: ADR-0001\n"
    "title: Use RabbitMQ\n"
    "status: accepted\n"
    "date: 2026-08-01\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths: []\n"
    "tags: []\n"
    "retrospective: false\n"
    "---\n\n"
    "    # Use RabbitMQ\n"
    "        Preserve this indentation.\n"
    "\n\n"
)

NEW_ADR = (
    "---\n"
    "id: ADR-0002\n"
    "title: Use Kafka\n"
    "status: accepted\n"
    "date: 2026-08-15\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths: []\n"
    "tags: []\n"
    "retrospective: false\n"
    "---\n\n"
    "  # Use Kafka\n"
    "    Keep this leading whitespace too.\n"
    "\n\n\n"
)


def _args(tmp_path, *, dry_run=False):
    return SimpleNamespace(adr_number=1, by=2, dir=str(tmp_path), dry_run=dry_run)


def test_supersede_updates_both_files_and_preserves_parsed_bodies(tmp_path):
    old_path = tmp_path / "0001-use-rabbitmq.md"
    new_path = tmp_path / "0002-use-kafka.md"
    old_path.write_text(OLD_ADR, encoding="utf-8")
    new_path.write_text(NEW_ADR, encoding="utf-8")
    old_body_before = fm.parse(old_path.read_text(encoding="utf-8"))[1]
    new_body_before = fm.parse(new_path.read_text(encoding="utf-8"))[1]

    result = supersede.run(_args(tmp_path))

    assert result["ok"] is True
    old_data, old_body_after = fm.parse(old_path.read_text(encoding="utf-8"))
    new_data, new_body_after = fm.parse(new_path.read_text(encoding="utf-8"))
    assert old_data["status"] == "superseded"
    assert old_data["superseded_by"] == "ADR-0002"
    assert new_data["supersedes"] == ["ADR-0001"]
    assert old_body_after == old_body_before
    assert new_body_after == new_body_before


def test_supersede_deduplicates_existing_new_adr_supersedes_list(tmp_path):
    (tmp_path / "0001-use-rabbitmq.md").write_text(OLD_ADR, encoding="utf-8")
    (tmp_path / "0002-use-kafka.md").write_text(
        NEW_ADR.replace(
            "retrospective: false\n",
            "retrospective: false\n"
            "supersedes:\n"
            "  - ADR-0001\n"
            "  - ADR-0099\n"
            "  - ADR-0001\n",
        ),
        encoding="utf-8",
    )

    result = supersede.run(_args(tmp_path))

    assert result["ok"] is True
    new_data, _ = fm.parse(
        (tmp_path / "0002-use-kafka.md").read_text(encoding="utf-8")
    )
    assert new_data["supersedes"] == ["ADR-0001", "ADR-0099"]


def test_supersede_missing_old_adr_is_reported(tmp_path):
    (tmp_path / "0002-use-kafka.md").write_text(NEW_ADR, encoding="utf-8")

    result = supersede.run(_args(tmp_path))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "ADR_NOT_FOUND"


def test_supersede_missing_new_adr_is_reported(tmp_path):
    (tmp_path / "0001-use-rabbitmq.md").write_text(OLD_ADR, encoding="utf-8")

    result = supersede.run(_args(tmp_path))

    assert result["ok"] is False
    assert result["errors"][0] == {"code": "ADR_NOT_FOUND", "id": 2}


def test_supersede_rejects_self_reference_without_writes(tmp_path):
    old_path = tmp_path / "0001-use-rabbitmq.md"
    old_path.write_text(OLD_ADR, encoding="utf-8")
    before = old_path.read_text(encoding="utf-8")

    result = supersede.run(
        SimpleNamespace(adr_number=1, by=1, dir=str(tmp_path), dry_run=False)
    )

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "SELF_SUPERSEDE"
    assert old_path.read_text(encoding="utf-8") == before


def test_supersede_invalid_transition_writes_neither_file(tmp_path):
    old_path = tmp_path / "0001-use-rabbitmq.md"
    new_path = tmp_path / "0002-use-kafka.md"
    old_path.write_text(OLD_ADR.replace("status: accepted", "status: proposed"), encoding="utf-8")
    new_path.write_text(NEW_ADR, encoding="utf-8")
    old_before = old_path.read_text(encoding="utf-8")
    new_before = new_path.read_text(encoding="utf-8")

    result = supersede.run(_args(tmp_path))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "INVALID_TRANSITION"
    assert old_path.read_text(encoding="utf-8") == old_before
    assert new_path.read_text(encoding="utf-8") == new_before


def test_supersede_rolls_back_old_file_when_new_file_write_fails(tmp_path, monkeypatch):
    old_path = tmp_path / "0001-use-rabbitmq.md"
    new_path = tmp_path / "0002-use-kafka.md"
    old_path.write_text(OLD_ADR, encoding="utf-8")
    new_path.write_text(NEW_ADR, encoding="utf-8")
    old_before = old_path.read_text(encoding="utf-8")
    new_before = new_path.read_text(encoding="utf-8")
    original_write_text = type(old_path).write_text

    def fail_new_file_write(path, text, *args, **kwargs):
        if path == new_path:
            raise OSError("simulated new ADR write failure")
        return original_write_text(path, text, *args, **kwargs)

    monkeypatch.setattr(type(old_path), "write_text", fail_new_file_write)

    with pytest.raises(OSError, match="simulated new ADR write failure"):
        supersede.run(_args(tmp_path))

    assert old_path.read_text(encoding="utf-8") == old_before
    assert new_path.read_text(encoding="utf-8") == new_before


def test_supersede_dry_run_writes_nothing(tmp_path):
    old_path = tmp_path / "0001-use-rabbitmq.md"
    new_path = tmp_path / "0002-use-kafka.md"
    old_path.write_text(OLD_ADR, encoding="utf-8")
    new_path.write_text(NEW_ADR, encoding="utf-8")
    old_before = old_path.read_text(encoding="utf-8")
    new_before = new_path.read_text(encoding="utf-8")

    result = supersede.run(_args(tmp_path, dry_run=True))

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert old_path.read_text(encoding="utf-8") == old_before
    assert new_path.read_text(encoding="utf-8") == new_before
