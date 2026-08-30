from types import SimpleNamespace

from scripts.commands import discover


def test_discover_reports_dependency_findings(tmp_path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    result = discover.run(SimpleNamespace(root=str(tmp_path)))
    assert result["ok"] is True
    assert {"ecosystem": "npm", "path": "package.json"} in result["dependencies"]


def test_discover_on_empty_repo_reports_no_dependencies(tmp_path):
    result = discover.run(SimpleNamespace(root=str(tmp_path)))
    assert result["dependencies"] == []
