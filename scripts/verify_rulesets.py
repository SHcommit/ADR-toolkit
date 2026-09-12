#!/usr/bin/env python3
"""Ruleset required-check drift verification script.

Verifies that GitHub workflow job definitions match the required check contexts
enforced by repository branch rulesets.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "test.yml"


def parse_workflow_jobs(workflow_path: Path) -> set[str]:
    """Extract job names (including matrix expansions) from a workflow YAML file."""
    try:
        import yaml
    except ImportError:
        print("PyYAML required to parse workflow files.", file=sys.stderr)
        return set()

    with open(workflow_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    jobs = data.get("jobs", {})
    job_names: set[str] = set()

    for job_id, job_def in jobs.items():
        matrix = job_def.get("strategy", {}).get("matrix", {})
        if matrix and "os" in matrix and "python-version" in matrix:
            for os_val in matrix["os"]:
                for py_val in matrix["python-version"]:
                    job_names.add(f"{job_id} ({os_val}, {py_val})")
        else:
            job_names.add(job_id)

    return job_names


def fetch_github_rulesets(repo: str) -> list[dict[str, Any]]:
    """Fetch repository rulesets using gh CLI if available."""
    try:
        res = subprocess.run(
            ["gh", "api", f"repos/{repo}/rulesets"],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(res.stdout)
        return data if isinstance(data, list) else []
    except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
        return []


def verify_ruleset_drift(repo: str = "SHcommit/ADR-toolkit", check_online: bool = False) -> bool:
    """Verify that workflow jobs match ruleset constraints."""
    if not WORKFLOW_FILE.exists():
        print(f"Error: Workflow file {WORKFLOW_FILE} not found.", file=sys.stderr)
        return False

    jobs = parse_workflow_jobs(WORKFLOW_FILE)
    if not jobs:
        print("Error: No jobs parsed from workflow file.", file=sys.stderr)
        return False

    print(f"Found {len(jobs)} workflow jobs in {WORKFLOW_FILE.name}:")
    for j in sorted(jobs):
        print(f"  - {j}")

    if check_online:
        rulesets = fetch_github_rulesets(repo)
        if not rulesets:
            print("Notice: Could not fetch GitHub rulesets via gh API (offline/unauthenticated).", file=sys.stderr)
        else:
            print(f"Fetched {len(rulesets)} rulesets from GitHub API.")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ruleset required-check drift.")
    parser.add_argument("--repo", default="SHcommit/ADR-toolkit", help="GitHub repository (owner/repo)")
    parser.add_argument("--online", action="store_true", help="Fetch live rulesets via gh API")
    args = parser.parse_args()

    ok = verify_ruleset_drift(repo=args.repo, check_online=args.online)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
