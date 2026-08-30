from types import SimpleNamespace

from scripts.commands import preflight


def test_reports_no_existing_adr_directory(tmp_path):
    result = preflight.run(SimpleNamespace(root=str(tmp_path)))
    assert result["ok"] is True
    assert result["existing_adr_directory"] is None


def test_detects_existing_docs_decisions_directory(tmp_path):
    (tmp_path / "docs" / "decisions").mkdir(parents=True)
    result = preflight.run(SimpleNamespace(root=str(tmp_path)))
    assert result["existing_adr_directory"] == "docs/decisions"


def test_reports_git_availability(tmp_path):
    result = preflight.run(SimpleNamespace(root=str(tmp_path)))
    assert isinstance(result["git_available"], bool)
