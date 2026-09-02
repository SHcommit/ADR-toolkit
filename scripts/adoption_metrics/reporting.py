"""Build and emit ADR adoption metric reports."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .calculation import _event_time, calculate_metrics
from .collection import (
    collect_git_events,
    collect_github_payload,
    merge_events,
    normalize_github_reviews,
    read_adrs,
    read_check_snapshot,
    read_events,
    read_exceptions,
    _run_git,
)
from .common import parse_timestamp

class CollectionError(Exception):
    def __init__(self, error: Dict[str, Any]):
        super().__init__(str(error))
        self.error = error


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CollectionError({"code": "INVALID_ARGUMENT", "detail": message})


def _resolve_within_root(root: Path, value: str) -> Path:
    candidate = Path(value)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise CollectionError({"code": "PATH_ESCAPES_ROOT", "path": str(resolved)})
    return resolved


def _default_since(
    adrs: List[Dict[str, Any]], events: List[Dict[str, Any]], until: datetime
) -> datetime:
    candidates: List[datetime] = []
    for event in events:
        try:
            candidates.append(_event_time(event))
        except (KeyError, TypeError, ValueError):
            continue
    for adr in adrs:
        try:
            candidates.append(parse_timestamp(str(adr["date"])))
        except (KeyError, TypeError, ValueError):
            continue
    return min(candidates) if candidates else until


def github_adr_paths(
    root: Path, adr_dir: Path, adrs: List[Dict[str, Any]]
) -> Dict[str, str]:
    top_result = _run_git(root, ["rev-parse", "--show-toplevel"])
    repository_root = (
        Path(top_result.stdout.strip()).resolve()
        if top_result.returncode == 0 and top_result.stdout.strip()
        else root
    )
    return {
        (adr_dir / str(adr["file"])).resolve().relative_to(repository_root).as_posix(): str(
            adr["id"]
        )
        for adr in adrs
    }


def build_report(
    root: Path,
    adr_dir: Path,
    since: Optional[datetime],
    until: datetime,
    event_paths: List[Path],
    check_paths: List[Path],
    use_github: bool,
) -> Dict[str, Any]:
    if not adr_dir.is_dir():
        raise CollectionError({"code": "ADR_DIR_NOT_FOUND", "path": str(adr_dir)})

    adrs, adr_warnings = read_adrs(adr_dir)
    exceptions, exception_warnings = read_exceptions(adr_dir)
    explicit_events, explicit_warnings = read_events(event_paths)
    current_violation_fingerprints, check_warnings = read_check_snapshot(
        check_paths, until
    )
    git_events, git_warnings = collect_git_events(root, adr_dir)

    github_events: List[Dict[str, Any]] = []
    github_warnings: List[Dict[str, Any]] = []
    if use_github:
        payload, github_warnings = collect_github_payload(root)
        if payload is not None:
            adr_paths = github_adr_paths(root, adr_dir, adrs)
            github_events, normalization_warnings = normalize_github_reviews(
                payload, adr_paths
            )
            github_warnings += normalization_warnings

    events, merge_warnings = merge_events(
        [
            ("events", explicit_events),
            ("git", git_events),
            ("github", github_events),
        ]
    )
    effective_since = since if since is not None else _default_since(adrs, events, until)
    if effective_since > until:
        raise CollectionError(
            {
                "code": "INVALID_PERIOD",
                "detail": "--since must be earlier than or equal to --until.",
            }
        )

    return {
        "ok": True,
        "operation": "adoption_metrics",
        "schema_version": 1,
        "period": {
            "since": effective_since.date().isoformat(),
            "until": until.date().isoformat(),
        },
        "metrics": calculate_metrics(
            adrs,
            exceptions,
            events,
            effective_since,
            until,
            current_violation_fingerprints,
        ),
        "warnings": (
            adr_warnings
            + exception_warnings
            + explicit_warnings
            + check_warnings
            + git_warnings
            + github_warnings
            + merge_warnings
        ),
    }


def _parse_cli_timestamp(value: Optional[str], option: str) -> Optional[datetime]:
    if value is None:
        return None
    try:
        return parse_timestamp(value)
    except ValueError:
        raise CollectionError(
            {"code": "INVALID_DATE", "option": option, "value": value}
        )


def _parser() -> JsonArgumentParser:
    parser = JsonArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--dir", default="docs/decisions")
    parser.add_argument("--since")
    parser.add_argument("--until")
    parser.add_argument("--events", action="append", default=[])
    parser.add_argument("--check-results", action="append", default=[])
    parser.add_argument("--github", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if not args.json:
            raise CollectionError(
                {"code": "JSON_REQUIRED", "detail": "--json is required."}
            )
        root = Path(args.root).resolve()
        adr_dir = _resolve_within_root(root, args.dir)
        event_paths = [_resolve_within_root(root, value) for value in args.events]
        check_paths = [
            _resolve_within_root(root, value) for value in args.check_results
        ]
        since = _parse_cli_timestamp(args.since, "--since")
        until = _parse_cli_timestamp(args.until, "--until")
        if until is None:
            now = datetime.now(timezone.utc)
            until = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        report = build_report(
            root,
            adr_dir,
            since,
            until,
            event_paths,
            check_paths,
            args.github,
        )
        return_code = 0
    except CollectionError as exc:
        report = {
            "ok": False,
            "operation": "adoption_metrics",
            "errors": [exc.error],
        }
        return_code = 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return return_code
