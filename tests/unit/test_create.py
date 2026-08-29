# tests/unit/test_create.py
import json
from pathlib import Path
from types import SimpleNamespace

from scripts.commands import create


def _write_draft(tmp_path, **overrides):
    draft = {
        "title": "Use Kafka for domain events",
        "status": "accepted",
        "body": "# Use Kafka for domain events\n\nBody text.\n",
    }
    draft.update(overrides)
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps(draft), encoding="utf-8")
    return draft_path


def test_creates_file_with_next_id_and_valid_frontmatter(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = _write_draft(tmp_path)

    result = create.run(SimpleNamespace(input=str(draft_path), dir=str(adr_dir), dry_run=False))

    assert result["ok"] is True
    assert result["id"] == "ADR-0001"
    created_file = Path(result["created"])
    assert created_file.name == "0001-use-kafka-for-domain-events.md"
    assert "status: accepted" in created_file.read_text(encoding="utf-8")


def test_next_id_accounts_for_existing_adrs(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-existing.md").write_text("x", encoding="utf-8")
    draft_path = _write_draft(tmp_path)

    result = create.run(SimpleNamespace(input=str(draft_path), dir=str(adr_dir), dry_run=False))

    assert result["id"] == "ADR-0002"


def test_dry_run_does_not_write_file(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = _write_draft(tmp_path)

    result = create.run(SimpleNamespace(input=str(draft_path), dir=str(adr_dir), dry_run=True))

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert list(adr_dir.iterdir()) == []


def test_missing_required_draft_field_is_an_error(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps({"title": "Missing status and body"}), encoding="utf-8")

    result = create.run(SimpleNamespace(input=str(draft_path), dir=str(adr_dir), dry_run=False))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "MISSING_DRAFT_FIELD"


def test_dry_run_against_nonexistent_dir_does_not_create_dir(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    # Note: adr_dir is NOT created beforehand
    draft_path = _write_draft(tmp_path)

    result = create.run(SimpleNamespace(input=str(draft_path), dir=str(adr_dir), dry_run=True))

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert not adr_dir.exists()


def test_dry_run_response_includes_id(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = _write_draft(tmp_path)

    result = create.run(SimpleNamespace(input=str(draft_path), dir=str(adr_dir), dry_run=True))

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert "id" in result
    assert result["id"] == "ADR-0001"


def test_empty_slug_title_is_an_error_and_does_not_write_file(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = _write_draft(tmp_path, title="아키텍처 결정 기록")

    result = create.run(SimpleNamespace(input=str(draft_path), dir=str(adr_dir), dry_run=False))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "EMPTY_SLUG"
    assert list(adr_dir.iterdir()) == []


def test_empty_slug_title_dry_run_is_also_an_error(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = _write_draft(tmp_path, title="아키텍처 결정 기록")

    result = create.run(SimpleNamespace(input=str(draft_path), dir=str(adr_dir), dry_run=True))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "EMPTY_SLUG"
    assert list(adr_dir.iterdir()) == []


def test_missing_draft_file_returns_json_error(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    missing_path = tmp_path / "does-not-exist.json"

    result = create.run(SimpleNamespace(input=str(missing_path), dir=str(adr_dir), dry_run=False))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "DRAFT_FILE_NOT_FOUND"


def test_malformed_json_draft_file_returns_json_error(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    bad_json_path = tmp_path / "draft.json"
    bad_json_path.write_text("{not valid json", encoding="utf-8")

    result = create.run(SimpleNamespace(input=str(bad_json_path), dir=str(adr_dir), dry_run=False))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "DRAFT_FILE_INVALID_JSON"
