#!/usr/bin/env python3
"""Collect provider-neutral ADR adoption metrics as deterministic JSON."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from adoption_metrics import collection as _collection
from adoption_metrics import reporting as _reporting
from adoption_metrics import (
    CollectionError,
    JsonArgumentParser,
    build_report as _build_report,
    calculate_metrics,
    collect_git_events,
    collect_github_payload as _collect_github_payload,
    github_adr_paths,
    main as _main,
    merge_events,
    normalize_github_reviews,
    parse_timestamp,
    read_adrs,
    read_check_snapshot,
    read_events,
    read_exceptions,
)

_run_gh = _collection._run_gh


def collect_github_payload(root):
    _collection._run_gh = _run_gh
    return _collect_github_payload(root)


def build_report(*args, **kwargs):
    _reporting.collect_github_payload = collect_github_payload
    return _build_report(*args, **kwargs)


def main(argv=None):
    _reporting.build_report = build_report
    return _main(argv)

__all__ = [
    "CollectionError",
    "JsonArgumentParser",
    "build_report",
    "calculate_metrics",
    "collect_git_events",
    "collect_github_payload",
    "github_adr_paths",
    "main",
    "merge_events",
    "normalize_github_reviews",
    "parse_timestamp",
    "read_adrs",
    "read_check_snapshot",
    "read_events",
    "read_exceptions",
    "_run_gh",
    "subprocess",
]

if __name__ == "__main__":
    sys.exit(main())
