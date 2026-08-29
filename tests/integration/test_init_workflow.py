import json
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "init_no_adr_js_project"
ADR_PY = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit" / "scripts" / "adr.py"


def _run(args, cwd):
    result = subprocess.run(
        [sys.executable, str(ADR_PY), *args], cwd=cwd, capture_output=True, text=True,
    )
    assert result.returncode in (0, 1), result.stderr
    return json.loads(result.stdout)


def test_full_init_flow_on_js_fixture(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)

    preflight = _run(["preflight", "--json"], cwd=repo)
    assert preflight["ok"] is True
    assert preflight["existing_adr_directory"] is None

    discovered = _run(["discover", "--json"], cwd=repo)
    assert {"ecosystem": "npm", "path": "package.json"} in discovered["dependencies"]

    init_result = _run(["init", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert init_result["ok"] is True

    validate_result = _run(["validate", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert validate_result["ok"] is True
    assert validate_result["checked"] == 1

    index_result = _run(["index", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert index_result["count"] == 1

    readme = (repo / "docs" / "decisions" / "README.md").read_text(encoding="utf-8")
    assert "ADR-0001" in readme
    assert "Accepted" in readme

    second_preflight = _run(["preflight", "--json"], cwd=repo)
    assert second_preflight["existing_adr_directory"] == "docs/decisions"
