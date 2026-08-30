from types import SimpleNamespace

from scripts.commands import validate

VALID_ADR = (
    "---\n"
    "id: ADR-0001\n"
    "title: Record architecture decisions\n"
    "status: accepted\n"
    "date: 2026-08-29\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths:\n"
    "  - docs/decisions/\n"
    "tags:\n"
    "  - process\n"
    "retrospective: false\n"
    "---\n\n"
    "# Record architecture decisions\n"
)


def test_valid_directory_passes(tmp_path):
    (tmp_path / "0001-record-architecture-decisions.md").write_text(VALID_ADR, encoding="utf-8")
    result = validate.run(SimpleNamespace(dir=str(tmp_path)))
    assert result["ok"] is True
    assert result["checked"] == 1
    assert result["errors"] == []


def test_duplicate_ids_are_reported(tmp_path):
    (tmp_path / "0001-a.md").write_text(VALID_ADR, encoding="utf-8")
    duplicate = VALID_ADR.replace("title: Record architecture decisions", "title: A duplicate")
    (tmp_path / "0002-b.md").write_text(duplicate, encoding="utf-8")

    result = validate.run(SimpleNamespace(dir=str(tmp_path)))

    assert result["ok"] is False
    assert any(e["code"] == "DUPLICATE_ADR_ID" for e in result["errors"])


def test_broken_related_link_is_reported(tmp_path):
    broken = VALID_ADR.replace("related: []", "related:\n  - ADR-0099")
    (tmp_path / "0001-a.md").write_text(broken, encoding="utf-8")

    result = validate.run(SimpleNamespace(dir=str(tmp_path)))

    assert result["ok"] is False
    assert any(e["code"] == "BROKEN_RELATED_LINK" for e in result["errors"])


def test_bad_filename_is_reported(tmp_path):
    (tmp_path / "not-a-valid-name.md").write_text(VALID_ADR, encoding="utf-8")
    result = validate.run(SimpleNamespace(dir=str(tmp_path)))
    assert any(e["code"] == "BAD_FILENAME" for e in result["errors"])


def test_filename_id_mismatch_is_reported(tmp_path):
    (tmp_path / "0002-something.md").write_text(VALID_ADR, encoding="utf-8")

    result = validate.run(SimpleNamespace(dir=str(tmp_path)))

    assert result["ok"] is False
    mismatches = [e for e in result["errors"] if e["code"] == "FILENAME_ID_MISMATCH"]
    assert len(mismatches) == 1
    assert mismatches[0]["file"] == "0002-something.md"
    assert mismatches[0]["expected_id"] == "ADR-0002"
    assert mismatches[0]["found_id"] == "ADR-0001"


def test_invalid_repository_config_fails_before_reporting_adr_success(tmp_path):
    (tmp_path / ".adr-toolkit.json").write_text(
        '{"schema_version": 1, "locale": "xx"}', encoding="utf-8"
    )
    adr_dir = tmp_path / "docs/decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-record-architecture-decisions.md").write_text(
        VALID_ADR, encoding="utf-8"
    )

    result = validate.run(SimpleNamespace(dir=str(adr_dir), root=str(tmp_path)))

    assert result["ok"] is False
    assert result["checked"] == 0
    assert result["errors"][0]["code"] == "CONFIG_ERROR"
