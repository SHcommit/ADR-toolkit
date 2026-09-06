
from scripts.evidence import dependency_scanner


def test_detects_npm_manifest(tmp_path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    findings = dependency_scanner.scan(tmp_path)
    assert {"ecosystem": "npm", "path": "package.json"} in findings


def test_detects_multiple_manifests(tmp_path):
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    (tmp_path / "go.mod").write_text("", encoding="utf-8")
    findings = dependency_scanner.scan(tmp_path)
    ecosystems = {f["ecosystem"] for f in findings}
    assert ecosystems == {"python", "go"}


def test_no_manifests_returns_empty_list(tmp_path):
    assert dependency_scanner.scan(tmp_path) == []
