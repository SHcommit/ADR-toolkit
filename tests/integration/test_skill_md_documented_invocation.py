"""Proves SKILL.md's documented invocation form resolves when run from the
repository root, as an agent following SKILL.md literally would run it.

SKILL.md tells the agent to run `python skills/adr-toolkit/scripts/adr.py
<op> ...` — a path relative to the repository root, not to
skills/adr-toolkit/ itself. This test invokes the CLI with exactly that
relative path and a cwd of the real repository root, using an absolute
--dir/--root so no repository state is touched.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCUMENTED_RELATIVE_SCRIPT_PATH = "skills/adr-toolkit/scripts/adr.py"


def _run(args):
    return subprocess.run(
        [sys.executable, DOCUMENTED_RELATIVE_SCRIPT_PATH, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_documented_relative_invocation_resolves_from_repo_root(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"

    preflight = _run(["preflight", "--json", "--root", str(tmp_path)])
    assert preflight.returncode == 0, preflight.stderr
    assert json.loads(preflight.stdout)["ok"] is True

    init_result = _run([
        "init", "--dir", str(adr_dir), "--root", str(tmp_path), "--json",
    ])
    assert init_result.returncode == 0, init_result.stderr
    assert json.loads(init_result.stdout)["ok"] is True

    validate_result = _run([
        "validate", "--dir", str(adr_dir), "--root", str(tmp_path), "--json",
    ])
    assert validate_result.returncode == 0, validate_result.stderr
    payload = json.loads(validate_result.stdout)
    assert payload["ok"] is True
    assert payload["checked"] == 1
