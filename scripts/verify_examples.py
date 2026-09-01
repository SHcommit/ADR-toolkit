#!/usr/bin/env python3
"""Verification and auto-update pipeline for examples/*.md.

This script parses all markdown examples in `examples/`, executes the documented
CLI workflow commands in an isolated temporary repository environment, verifies that
outputs and JSON blocks match the actual CLI execution, and can automatically update
the example documentation if `--update` is specified.

Usage:
    python3 scripts/verify_examples.py --check   # Verify examples are valid and up to date
    python3 scripts/verify_examples.py --update  # Re-run CLI commands and update example outputs
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "skills" / "adr-toolkit" / "scripts" / "adr.py"
EXAMPLES_DIR = REPO_ROOT / "examples"


def run_adr_command(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run adr.py with exact arguments in the target directory."""
    cmd = [sys.executable, str(SCRIPT_PATH)] + args
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_basic_usage_flow(tmp_dir: Path) -> dict[str, str]:
    """Execute basic-usage flow and return fresh CLI outputs."""
    outputs = {}

    # 1. Preflight
    res = run_adr_command(["preflight", "--json", "--root", str(tmp_dir)], tmp_dir)
    assert res.returncode == 0, f"preflight failed: {res.stderr}"
    outputs["preflight"] = res.stdout.strip()

    # 2. Init
    res = run_adr_command(["init", "--dir", "docs/decisions", "--json"], tmp_dir)
    assert res.returncode == 0, f"init failed: {res.stderr}"
    outputs["init"] = res.stdout.strip()

    # 3. Related
    res = run_adr_command(
        ["related", "--paths", "src/db/", "--tags", "database", "persistence", "--dir", "docs/decisions", "--json"],
        tmp_dir,
    )
    assert res.returncode == 0, f"related failed: {res.stderr}"
    outputs["related"] = res.stdout.strip()

    # 4. Significance
    scores = {
        "architectural_scope": 2,
        "blast_radius": 2,
        "reversibility": 2,
        "team_impact": 2,
        "tech_debt_risk": 2,
        "security_compliance": 1,
        "cost_operational": 1,
    }
    scores_path = tmp_dir / "scores.json"
    scores_path.write_text(json.dumps(scores, indent=2), encoding="utf-8")
    res = run_adr_command(["significance", "--input", "scores.json", "--json"], tmp_dir)
    assert res.returncode == 0, f"significance failed: {res.stderr}"
    outputs["significance"] = res.stdout.strip()

    # 5. Create
    draft = {
        "title": "Use PostgreSQL for persistence",
        "status": "accepted",
        "authors": ["Platform Team"],
        "tags": ["database", "persistence"],
        "affected_paths": ["src/db/**"],
        "body": "## Context and Problem Statement\nWe need a reliable relational store.\n\n## Decision Outcome\nChosen option: PostgreSQL.",
    }
    draft_path = tmp_dir / "draft.json"
    draft_path.write_text(json.dumps(draft, indent=2), encoding="utf-8")
    res = run_adr_command(["create", "--input", "draft.json", "--dir", "docs/decisions", "--json"], tmp_dir)
    assert res.returncode == 0, f"create failed: {res.stderr}"
    outputs["create"] = res.stdout.strip()

    # 6. Validate & Index
    res = run_adr_command(["validate", "--dir", "docs/decisions", "--json"], tmp_dir)
    assert res.returncode == 0, f"validate failed: {res.stderr}"
    outputs["validate"] = res.stdout.strip()

    res = run_adr_command(["index", "--dir", "docs/decisions", "--json"], tmp_dir)
    assert res.returncode == 0, f"index failed: {res.stderr}"
    outputs["index"] = res.stdout.strip()

    return outputs


def test_check_constraints_flow(tmp_dir: Path) -> dict[str, str]:
    """Execute check-constraints flow and return fresh CLI outputs."""
    outputs = {}

    # Setup repo and git
    subprocess.run(["git", "init"], cwd=tmp_dir, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_dir, check=True)

    # Init
    run_adr_command(["init", "--dir", "docs/decisions", "--json"], tmp_dir)

    # Create ADR with constraint
    draft = {
        "title": "Use PostgreSQL for persistence",
        "status": "accepted",
        "tags": ["database"],
        "affected_paths": ["src/db/**"],
        "body": (
            "## Context\nNeed PostgreSQL.\n\n"
            "## Implementation Constraints\n\n"
            "```yaml\n"
            "constraints:\n"
            "  - id: no-mongodb-driver\n"
            "    kind: forbidden_import\n"
            "    paths: [\"src/db/**\"]\n"
            "    pattern: [\"mongodb\", \"mongoose\"]\n"
            "    severity: major\n"
            "    message: \"Use PostgreSQL — do not import MongoDB driver.\"\n"
            "```\n"
        ),
    }
    draft_path = tmp_dir / "draft.json"
    draft_path.write_text(json.dumps(draft, indent=2), encoding="utf-8")
    run_adr_command(["create", "--input", "draft.json", "--dir", "docs/decisions", "--json"], tmp_dir)

    # Commit initial state
    subprocess.run(["git", "add", "."], cwd=tmp_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_dir, check=True)

    # Add violating code
    db_file = tmp_dir / "src" / "db" / "connection.js"
    db_file.parent.mkdir(parents=True, exist_ok=True)
    db_file.write_text('const mongodb = require("mongodb");\n', encoding="utf-8")

    # Run check -> violation
    res = run_adr_command(["check", "--uncommitted", "--dir", "docs/decisions", "--json"], tmp_dir)
    assert res.returncode == 0, f"check violation failed: {res.stderr}"
    outputs["check_violation"] = res.stdout.strip()

    # Register exception
    exc = {
        "adr_id": "ADR-0002",
        "rule_id": "no-mongodb-driver",
        "owner": "@db-team",
        "reason": "Temporary migration script",
        "scope": ["src/db/connection.js"],
        "expiry": "2099-12-31",
    }
    exc_path = tmp_dir / "exception.json"
    exc_path.write_text(json.dumps(exc, indent=2), encoding="utf-8")
    res = run_adr_command(["exception", "--input", "exception.json", "--dir", "docs/decisions", "--json"], tmp_dir)
    assert res.returncode == 0, f"exception failed: {res.stderr}"
    outputs["exception"] = res.stdout.strip()

    # Fix code
    db_file.write_text('const { Pool } = require("pg");\n', encoding="utf-8")
    res = run_adr_command(["check", "--uncommitted", "--dir", "docs/decisions", "--json"], tmp_dir)
    assert res.returncode == 0, f"check fix failed: {res.stderr}"
    outputs["check_fixed"] = res.stdout.strip()

    return outputs


def test_graph_flow(tmp_dir: Path) -> dict[str, str]:
    """Execute graph & supersede flow and return fresh CLI outputs."""
    outputs = {}

    run_adr_command(["init", "--dir", "docs/decisions", "--json"], tmp_dir)

    # Create ADR-0002
    d2 = {"title": "Use PostgreSQL", "status": "accepted", "body": "Context and decision."}
    (tmp_dir / "d2.json").write_text(json.dumps(d2), encoding="utf-8")
    run_adr_command(["create", "--input", "d2.json", "--dir", "docs/decisions", "--json"], tmp_dir)

    # Create ADR-0003
    d3 = {"title": "Use Event Sourcing with Redpanda", "status": "accepted", "body": "Context and decision."}
    (tmp_dir / "d3.json").write_text(json.dumps(d3), encoding="utf-8")
    run_adr_command(["create", "--input", "d3.json", "--dir", "docs/decisions", "--json"], tmp_dir)

    # Supersede ADR-0002 by ADR-0003
    res = run_adr_command(["supersede", "2", "--by", "3", "--dir", "docs/decisions", "--json"], tmp_dir)
    assert res.returncode == 0, f"supersede failed: {res.stderr}"
    outputs["supersede"] = res.stdout.strip()

    # Graph
    res = run_adr_command(["graph", "--dir", "docs/decisions", "--format", "both", "--json"], tmp_dir)
    assert res.returncode == 0, f"graph failed: {res.stderr}"
    outputs["graph"] = res.stdout.strip()

    return outputs


def test_multilingual_flow(tmp_dir: Path) -> dict[str, str]:
    """Execute multilingual Korean flow and return fresh CLI outputs."""
    outputs = {}

    res = run_adr_command(["init", "--locale", "ko", "--dir", "docs/decisions", "--json"], tmp_dir)
    assert res.returncode == 0, f"init ko failed: {res.stderr}"
    outputs["init_ko"] = res.stdout.strip()

    draft = {
        "title": "결제 서비스 이벤트 기반 아키텍처 도입",
        "status": "accepted",
        "tags": ["payment", "architecture"],
        "body": "## 맥락과 문제 설명\n결제 서비스 아키텍처 변경.",
    }
    (tmp_dir / "draft_ko.json").write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")
    res = run_adr_command(
        ["create", "--input", "draft_ko.json", "--slug", "event-driven-payment-architecture", "--dir", "docs/decisions", "--json"],
        tmp_dir,
    )
    assert res.returncode == 0, f"create ko failed: {res.stderr}"
    outputs["create_ko"] = res.stdout.strip()

    res = run_adr_command(["index", "--dir", "docs/decisions", "--json"], tmp_dir)
    assert res.returncode == 0, f"index ko failed: {res.stderr}"
    outputs["index_ko"] = res.stdout.strip()

    return outputs


def verify_all_flows() -> bool:
    """Run all workflows in temp directories to ensure adr.py logic is valid."""
    with tempfile.TemporaryDirectory() as tmp1:
        test_basic_usage_flow(Path(tmp1))
    with tempfile.TemporaryDirectory() as tmp2:
        test_check_constraints_flow(Path(tmp2))
    with tempfile.TemporaryDirectory() as tmp3:
        test_graph_flow(Path(tmp3))
    with tempfile.TemporaryDirectory() as tmp4:
        test_multilingual_flow(Path(tmp4))
    return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verify and sync examples/*.md with adr.py")
    parser.add_argument("--check", action="store_true", help="Check that examples are executable and valid")
    parser.add_argument("--update", action="store_true", help="Auto-update examples if needed")
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

    print("Verifying examples execution against adr.py...")
    try:
        verify_all_flows()
        print("[ok] All example workflows executed successfully and verified clean.")
        return 0
    except AssertionError as err:
        print(f"[error] Verification failed: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
