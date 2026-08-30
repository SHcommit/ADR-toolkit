import json
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "check_provider_port"
ADR_PY = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit" / "scripts" / "adr.py"


def _run(args, cwd):
    command = [sys.executable, str(ADR_PY), *args]
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    assert result.returncode == 0, (
        f"CLI command failed: {' '.join(command)}\n"
        f"cwd: {cwd}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"CLI command did not return JSON: {' '.join(command)}\n"
            f"cwd: {cwd}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        ) from exc
    assert payload.get("ok") is True, (
        f"CLI command reported failure: {' '.join(command)}\ncwd: {cwd}\npayload: {payload!r}"
    )
    return payload


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_check_flags_a_violation_then_clears_after_the_fix(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)
    _git(["init", "-q", "-b", "master"], repo)
    _git(["config", "user.email", "test@example.com"], repo)
    _git(["config", "user.name", "Test"], repo)
    _git(["add", "-A"], repo)
    _git(["commit", "-q", "-m", "init"], repo)

    features_dir = repo / "src" / "features"
    features_dir.mkdir(parents=True)
    (features_dir / "chat.py").write_text("import openai\n\ndef handler():\n    pass\n", encoding="utf-8")

    violating_result = _run(
        ["check", "--uncommitted", "--dir", "docs/decisions", "--json"], cwd=repo,
    )
    violation = next(f for f in violating_result["findings"] if f["kind"] == "verified_violation")
    assert violation["adr_id"] == "ADR-0001"
    assert violation["rule_id"] == "no-provider-sdk-in-feature"
    assert set(violation["resolutions"]) == {
        "fix_code", "supersede_adr", "adjust_scope", "register_exception", "false_positive",
    }

    (features_dir / "chat.py").write_text(
        "from src.core.ports.llm import LLMPort\n\ndef handler():\n    pass\n", encoding="utf-8",
    )

    fixed_result = _run(
        ["check", "--uncommitted", "--dir", "docs/decisions", "--json"], cwd=repo,
    )
    assert all(f["kind"] != "verified_violation" for f in fixed_result["findings"])
    related = next(f for f in fixed_result["findings"] if f["adr_id"] == "ADR-0001")
    assert related["kind"] == "related"
