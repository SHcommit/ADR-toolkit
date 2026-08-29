import json
import subprocess
import sys
from pathlib import Path

ADR_PY = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit" / "scripts" / "adr.py"


def _run(args, cwd):
    return subprocess.run(
        [sys.executable, str(ADR_PY), *args], cwd=cwd, capture_output=True, text=True,
    )


def test_preflight_returns_valid_json(tmp_path):
    result = _run(["preflight", "--json"], cwd=tmp_path)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["operation"] == "preflight"
    assert payload["ok"] is True


def test_init_then_validate_round_trip(tmp_path):
    init_result = _run(["init", "--dir", "docs/decisions", "--json"], cwd=tmp_path)
    assert init_result.returncode == 0

    validate_result = _run(["validate", "--dir", "docs/decisions", "--json"], cwd=tmp_path)
    payload = json.loads(validate_result.stdout)
    assert validate_result.returncode == 0
    assert payload["ok"] is True
    assert payload["checked"] == 1


def test_unknown_subcommand_exits_nonzero(tmp_path):
    result = _run(["not-a-real-command"], cwd=tmp_path)
    assert result.returncode != 0
