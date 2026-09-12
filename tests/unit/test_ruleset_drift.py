"""Unit tests for ruleset required-check drift verification script."""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_rulesets.py"
WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "test.yml"

spec = importlib.util.spec_from_file_location("verify_rulesets", SCRIPT_PATH)
assert spec is not None and spec.loader is not None
verify_rulesets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_rulesets)


def test_parse_workflow_jobs() -> None:
    jobs = verify_rulesets.parse_workflow_jobs(WORKFLOW_FILE)
    assert "lint" in jobs
    assert "dependency-audit" in jobs
    assert "version-drift" in jobs
    assert "harness-parity" in jobs
    assert "pytest (ubuntu-latest, 3.10)" in jobs
    assert "pytest (ubuntu-latest, 3.12)" in jobs


def test_verify_ruleset_drift_local() -> None:
    assert verify_rulesets.verify_ruleset_drift(check_online=False) is True
