from types import SimpleNamespace

from scripts.commands import init


def test_dry_run_reports_would_create_without_writing(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    result = init.run(SimpleNamespace(dir=str(adr_dir), dry_run=True))
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert not adr_dir.exists()


def test_creates_directory_template_and_first_adr(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    result = init.run(SimpleNamespace(dir=str(adr_dir), dry_run=False))
    assert result["ok"] is True
    assert (adr_dir / "adr-template.md").is_file()
    first_adr = adr_dir / "0001-record-architecture-decisions.md"
    assert first_adr.is_file()
    content = first_adr.read_text(encoding="utf-8")
    assert "id: ADR-0001" in content
    assert "status: accepted" in content


def test_refuses_to_run_on_non_empty_directory(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "existing.md").write_text("x", encoding="utf-8")

    result = init.run(SimpleNamespace(dir=str(adr_dir), dry_run=False))
    assert result["ok"] is False
    assert result["errors"][0]["code"] == "ADR_DIRECTORY_NOT_EMPTY"
