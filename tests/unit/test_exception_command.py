import json
from types import SimpleNamespace

from scripts.commands import exception

VALID_DRAFT = {
    "adr_id": "ADR-0001",
    "rule_id": "no-provider-sdk-in-feature",
    "owner": "YangSeungHyun",
    "reason": "Vendor migration is in progress; tracked in issue #42.",
    "scope": ["src/features/legacy/**"],
    "expiry": "2026-12-31",
}


def _args(tmp_path, draft, **overrides):
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps(draft), encoding="utf-8")
    defaults = dict(
        input=str(draft_path), dir="docs/decisions", root=str(tmp_path), dry_run=False,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_creates_first_exception_as_exc_0001(tmp_path):
    result = exception.run(_args(tmp_path, VALID_DRAFT))

    assert result["ok"] is True
    assert result["id"] == "EXC-0001"
    created = tmp_path / "docs" / "decisions" / "exceptions" / "0001.json"
    assert created.is_file()
    data = json.loads(created.read_text(encoding="utf-8"))
    assert data["id"] == "EXC-0001"
    assert data["adr_id"] == "ADR-0001"
    assert data["owner"] == "YangSeungHyun"
    assert data["created"]  # auto-stamped


def test_second_exception_gets_next_sequential_id(tmp_path):
    exception.run(_args(tmp_path, VALID_DRAFT))
    second_draft = {**VALID_DRAFT, "rule_id": "some-other-rule"}

    result = exception.run(_args(tmp_path, second_draft))

    assert result["id"] == "EXC-0002"
    assert (tmp_path / "docs" / "decisions" / "exceptions" / "0002.json").is_file()


def test_missing_required_field_fails_before_writing(tmp_path):
    bad_draft = {k: v for k, v in VALID_DRAFT.items() if k != "owner"}

    result = exception.run(_args(tmp_path, bad_draft))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "MISSING_DRAFT_FIELD"
    assert not (tmp_path / "docs" / "decisions" / "exceptions").exists()


def test_present_but_invalid_field_fails_with_schema_error(tmp_path):
    bad_draft = {**VALID_DRAFT, "expiry": "not-a-date"}

    result = exception.run(_args(tmp_path, bad_draft))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "SCHEMA_ERROR"
    assert not (tmp_path / "docs" / "decisions" / "exceptions").exists()


def test_dry_run_validates_without_writing(tmp_path):
    result = exception.run(_args(tmp_path, VALID_DRAFT, dry_run=True))

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert not (tmp_path / "docs" / "decisions" / "exceptions").exists()


def test_missing_input_file_is_an_explicit_error(tmp_path):
    args = SimpleNamespace(
        input=str(tmp_path / "nope.json"), dir="docs/decisions", root=str(tmp_path),
        dry_run=False,
    )

    result = exception.run(args)

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "DRAFT_FILE_NOT_FOUND"
