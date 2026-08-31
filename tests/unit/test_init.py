from types import SimpleNamespace
import json

from scripts.commands import init


def test_dry_run_reports_would_create_without_writing(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    result = init.run(SimpleNamespace(
        dir=str(adr_dir), root=str(tmp_path), locale=None, dry_run=True,
    ))
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert not adr_dir.exists()


def test_creates_directory_template_and_first_adr(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    result = init.run(SimpleNamespace(
        dir=str(adr_dir), root=str(tmp_path), locale=None, dry_run=False,
    ))
    assert result["ok"] is True
    assert (adr_dir / "adr-template.md").is_file()
    first_adr = adr_dir / "0001-record-architecture-decisions.md"
    assert first_adr.is_file()
    content = first_adr.read_text(encoding="utf-8")
    assert "id: ADR-0001" in content
    assert "status: accepted" in content


def test_affected_paths_and_confirmation_reflect_custom_dir(tmp_path):
    adr_dir = tmp_path / "custom" / "adr-location"
    result = init.run(SimpleNamespace(
        dir=str(adr_dir), root=str(tmp_path), locale=None, dry_run=False,
    ))
    assert result["ok"] is True

    content = (adr_dir / "0001-record-architecture-decisions.md").read_text(encoding="utf-8")
    expected_path = str(adr_dir).rstrip("/") + "/"
    assert f"  - {expected_path}\n" in content
    assert "docs/decisions/" not in content
    assert f"`{expected_path}` exists with this file" in content


def test_refuses_to_run_on_non_empty_directory(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "existing.md").write_text("x", encoding="utf-8")

    result = init.run(SimpleNamespace(
        dir=str(adr_dir), root=str(tmp_path), locale=None, dry_run=False,
    ))
    assert result["ok"] is False
    assert result["errors"][0]["code"] == "ADR_DIRECTORY_NOT_EMPTY"
    assert not (tmp_path / ".adr-toolkit.json").exists()


def test_init_creates_config_and_korean_scaffold(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"

    result = init.run(SimpleNamespace(
        dir=str(adr_dir), root=str(tmp_path), locale="ko", dry_run=False,
    ))

    assert result["ok"] is True
    config = json.loads((tmp_path / ".adr-toolkit.json").read_text(encoding="utf-8"))
    assert config == {"schema_version": 1, "locale": "ko"}
    adr = (adr_dir / "0001-record-architecture-decisions.md").read_text(encoding="utf-8")
    assert "locale: ko" in adr
    assert "## 맥락 및 문제 설명" in adr
    assert "# 아키텍처 결정을 기록한다" in adr


def test_init_dry_run_lists_config_without_writing(tmp_path):
    config_path = tmp_path / ".adr-toolkit.json"

    result = init.run(SimpleNamespace(
        dir=str(tmp_path / "docs/decisions"),
        root=str(tmp_path),
        locale="fr",
        dry_run=True,
    ))

    assert str(config_path) in result["would_create"]
    assert not config_path.exists()


def test_init_never_overwrites_existing_config(tmp_path):
    config = tmp_path / ".adr-toolkit.json"
    config.write_text(
        json.dumps({"schema_version": 1, "locale": "ja"}), encoding="utf-8"
    )

    result = init.run(SimpleNamespace(
        dir=str(tmp_path / "docs/decisions"),
        root=str(tmp_path),
        locale=None,
        dry_run=False,
    ))

    assert result["ok"] is True
    assert json.loads(config.read_text(encoding="utf-8"))["locale"] == "ja"
    adr = (tmp_path / "docs/decisions/0001-record-architecture-decisions.md").read_text(encoding="utf-8")
    assert "locale: ja" in adr
    assert "## コンテキストと問題" in adr


def test_relative_adr_directory_is_resolved_against_root(tmp_path, monkeypatch):
    caller = tmp_path / "caller"
    repo = tmp_path / "repo"
    caller.mkdir()
    repo.mkdir()
    monkeypatch.chdir(caller)

    result = init.run(SimpleNamespace(
        dir="docs/decisions", root=str(repo), locale="ko", dry_run=False,
    ))

    assert result["ok"] is True
    assert (repo / ".adr-toolkit.json").is_file()
    assert (repo / "docs/decisions/0001-record-architecture-decisions.md").is_file()
    assert not (caller / "docs/decisions").exists()
