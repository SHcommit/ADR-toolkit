# tests/unit/test_create.py
import json
from pathlib import Path
from types import SimpleNamespace

from scripts.commands import create
from scripts.core import frontmatter as fm


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


def _args(tmp_path, draft_path, adr_dir, *, dry_run=False, locale=None, slug=None):
    return SimpleNamespace(
        interactive=False,
        input=str(draft_path),
        dir=str(adr_dir),
        root=str(tmp_path),
        locale=locale,
        slug=slug,
        dry_run=dry_run,
    )


def test_creates_file_with_next_id_and_valid_frontmatter(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = _write_draft(tmp_path)

    result = create.run(_args(tmp_path, draft_path, adr_dir))

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

    result = create.run(_args(tmp_path, draft_path, adr_dir))

    assert result["id"] == "ADR-0002"


def test_dry_run_does_not_write_file(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = _write_draft(tmp_path)

    result = create.run(_args(tmp_path, draft_path, adr_dir, dry_run=True))

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert list(adr_dir.iterdir()) == []


def test_missing_required_draft_field_is_an_error(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps({"title": "Missing status and body"}), encoding="utf-8")

    result = create.run(_args(tmp_path, draft_path, adr_dir))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "MISSING_DRAFT_FIELD"


def test_dry_run_against_nonexistent_dir_does_not_create_dir(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    # Note: adr_dir is NOT created beforehand
    draft_path = _write_draft(tmp_path)

    result = create.run(_args(tmp_path, draft_path, adr_dir, dry_run=True))

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert not adr_dir.exists()


def test_dry_run_response_includes_id(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = _write_draft(tmp_path)

    result = create.run(_args(tmp_path, draft_path, adr_dir, dry_run=True))

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert "id" in result
    assert result["id"] == "ADR-0001"


def test_non_ascii_title_uses_portable_fallback_filename(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = _write_draft(tmp_path, title="아키텍처 결정 기록")

    result = create.run(_args(tmp_path, draft_path, adr_dir))

    assert result["ok"] is True
    assert Path(result["created"]).name == "0001-decision.md"


def test_non_ascii_title_dry_run_reports_portable_fallback(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = _write_draft(tmp_path, title="아키텍처 결정 기록")

    result = create.run(_args(tmp_path, draft_path, adr_dir, dry_run=True))

    assert result["ok"] is True
    assert result["would_create"].endswith("0001-decision.md")
    assert list(adr_dir.iterdir()) == []


def test_missing_draft_file_returns_json_error(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    missing_path = tmp_path / "does-not-exist.json"

    result = create.run(_args(tmp_path, missing_path, adr_dir))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "DRAFT_FILE_NOT_FOUND"


def test_malformed_json_draft_file_returns_json_error(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    bad_json_path = tmp_path / "draft.json"
    bad_json_path.write_text("{not valid json", encoding="utf-8")

    result = create.run(_args(tmp_path, bad_json_path, adr_dir))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "DRAFT_FILE_INVALID_JSON"


def test_input_create_uses_repo_locale_and_semantic_slug(tmp_path):
    (tmp_path / ".adr-toolkit.json").write_text(
        json.dumps({"schema_version": 1, "locale": "ko"}), encoding="utf-8"
    )
    adr_dir = tmp_path / "docs/decisions"
    draft_path = _write_draft(
        tmp_path,
        title="결제 시스템 분리",
        slug="separate-payment-system",
        body="# 결제 시스템 분리\n",
    )

    result = create.run(_args(tmp_path, draft_path, adr_dir))

    assert result["created"].endswith("0001-separate-payment-system.md")
    assert "locale: ko" in Path(result["created"]).read_text(encoding="utf-8")


def test_cli_locale_overrides_draft_and_repo(tmp_path):
    result = _run_with_locales(tmp_path, repo="ko", draft="fr", cli="ja")
    data, _ = fm.parse(Path(result["created"]).read_text(encoding="utf-8"))
    assert data["locale"] == "ja"


def test_draft_locale_overrides_repo(tmp_path):
    result = _run_with_locales(tmp_path, repo="ko", draft="fr", cli=None)
    data, _ = fm.parse(Path(result["created"]).read_text(encoding="utf-8"))
    assert data["locale"] == "fr"


def _run_with_locales(tmp_path, *, repo, draft, cli):
    (tmp_path / ".adr-toolkit.json").write_text(
        json.dumps({"schema_version": 1, "locale": repo}), encoding="utf-8"
    )
    adr_dir = tmp_path / "docs/decisions"
    draft_path = _write_draft(tmp_path, locale=draft)
    return create.run(_args(tmp_path, draft_path, adr_dir, locale=cli))


def test_invalid_explicit_slug_returns_structured_error(tmp_path):
    adr_dir = tmp_path / "docs/decisions"
    draft_path = _write_draft(tmp_path, title="한국어 제목", slug="Bad Slug")

    result = create.run(_args(tmp_path, draft_path, adr_dir))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "INVALID_SLUG"


def test_conflicting_cli_and_draft_slugs_return_structured_error(tmp_path):
    adr_dir = tmp_path / "docs/decisions"
    draft_path = _write_draft(tmp_path, slug="draft-slug")

    result = create.run(_args(tmp_path, draft_path, adr_dir, slug="cli-slug"))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "CONFLICTING_SLUG_INPUT"
