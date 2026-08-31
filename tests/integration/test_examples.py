"""Integration test verifying that examples/*.md workflows remain executable and up-to-date with adr.py logic.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VERIFY_SCRIPT = REPO_ROOT / "scripts" / "verify_examples.py"


def test_examples_execution_and_schema_parity():
    """Verify that all example workflows execute cleanly without error."""
    res = subprocess.run(
        [sys.executable, str(VERIFY_SCRIPT), "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Example verification script failed:\nstdout: {res.stdout}\nstderr: {res.stderr}"
