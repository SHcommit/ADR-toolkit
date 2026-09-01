#!/usr/bin/env python3
"""Collect provider-neutral ADR adoption metrics as deterministic JSON."""

import argparse
import hashlib
import json
import re
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
REQUIRED_EXCEPTION_FIELDS = {
    "id",
    "adr_id",
    "rule_id",
    "owner",
    "reason",
    "scope",
    "created",
    "expiry",
}
EXCEPTION_FIELD_TYPES = {
    "id": str,
    "adr_id": str,
    "rule_id": str,
    "owner": str,
    "reason": str,
    "scope": list,
    "created": str,
    "expiry": str,
}
EXCEPTION_ID_RE = re.compile(r"^EXC-\d{4}$")
ADR_ID_RE = re.compile(r"^ADR-\d{4}$")
DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EVENT_REQUIRED_FIELDS = {
    "adr_created": {"adr_id", "status"},
    "adr_status_changed": {"adr_id", "from", "to"},
    "review_requested": {"adr_id", "reviewer", "review_cycle"},
    "review_submitted": {"adr_id", "reviewer", "review_cycle", "qualified"},
    "violation_observed": {"fingerprint", "adr_id", "rule_id"},
    "violation_resolved": {"fingerprint", "adr_id", "rule_id"},
}
GITHUB_REVIEW_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 100, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        id
        number
        author { login }
        files(first: 100) { nodes { path } pageInfo { hasNextPage } }
        timelineItems(
          first: 100,
          itemTypes: [REVIEW_REQUESTED_EVENT, PULL_REQUEST_REVIEW]
        ) {
          nodes {
            __typename
            ... on ReviewRequestedEvent {
              createdAt
              requestedReviewer {
                __typename
                ... on User { login }
                ... on Team { slug }
                ... on Mannequin { login }
              }
            }
            ... on PullRequestReview {
              submittedAt
              author { login }
            }
          }
          pageInfo { hasNextPage }
        }
      }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""


def _parse_scalar_frontmatter(text: str) -> Dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if match is None:
        raise ValueError("No YAML frontmatter block found")

    data: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.startswith("  - "):
            continue
        if ":" not in line:
            raise ValueError("Malformed frontmatter line: {!r}".format(line))
        key, value = line.split(":", 1)
        value = value.strip()
        if value:
            data[key.strip()] = value.strip('"').strip("'")
    return data


def read_adrs(adr_dir: Path) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    records: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []
    for path in sorted(adr_dir.glob("[0-9]*.md")):
        try:
            data = _parse_scalar_frontmatter(path.read_text(encoding="utf-8"))
            for field in ("id", "title", "status", "date"):
                if not data.get(field):
                    raise ValueError("missing required field: {}".format(field))
            try:
                parse_timestamp(data["date"])
            except ValueError as exc:
                raise ValueError("invalid date: {}".format(exc))
        except (OSError, UnicodeError, ValueError) as exc:
            warnings.append(
                {"code": "BAD_FRONTMATTER", "file": path.name, "detail": str(exc)}
            )
            continue
        records.append(
            {
                "id": data["id"],
                "title": data["title"],
                "status": data["status"],
                "date": data["date"],
                "file": path.name,
            }
        )
    return records, warnings


def read_exceptions(adr_dir: Path) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    records: List[Dict[str, Any]] = []
    warnings: List[Dict[str, str]] = []
    exceptions_dir = adr_dir / "exceptions"
    if not exceptions_dir.is_dir():
        return records, warnings

    for path in sorted(exceptions_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("exception must be a JSON object")
            missing = sorted(REQUIRED_EXCEPTION_FIELDS - set(data))
            if missing:
                raise ValueError("missing required field(s): {}".format(", ".join(missing)))
            for field, expected_type in EXCEPTION_FIELD_TYPES.items():
                if not isinstance(data[field], expected_type):
                    raise ValueError(
                        "field {!r} must be {}, got {}".format(
                            field, expected_type.__name__, type(data[field]).__name__
                        )
                    )
            if not EXCEPTION_ID_RE.fullmatch(data["id"]):
                raise ValueError("id does not match EXC-NNNN")
            if not ADR_ID_RE.fullmatch(data["adr_id"]):
                raise ValueError("adr_id does not match ADR-NNNN")
            for field in ("owner", "reason", "rule_id"):
                if not data[field].strip():
                    raise ValueError("{} must not be empty".format(field))
            if not data["scope"]:
                raise ValueError("scope must contain at least one path pattern")
            if not all(isinstance(item, str) for item in data["scope"]):
                raise ValueError("scope items must be strings")
            for field in ("created", "expiry"):
                if not DATE_ONLY_RE.fullmatch(data[field]):
                    raise ValueError("{} must be YYYY-MM-DD".format(field))
                try:
                    parse_timestamp(str(data[field]))
                except ValueError as exc:
                    raise ValueError("invalid {}: {}".format(field, exc))
        except (json.JSONDecodeError, OSError, UnicodeError, ValueError) as exc:
            warnings.append(
                {"code": "BAD_EXCEPTION", "file": path.name, "detail": str(exc)}
            )
            continue
        records.append(data)
    return records, warnings


def parse_timestamp(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _validate_event(data: Any) -> None:
    if not isinstance(data, dict):
        raise ValueError("event must be a JSON object")
    if data.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    event_name = data.get("event")
    if event_name not in EVENT_REQUIRED_FIELDS:
        raise ValueError("unknown event: {!r}".format(event_name))
    missing = (
        {"occurred_at", "source"} | EVENT_REQUIRED_FIELDS[str(event_name)]
    ) - set(data)
    if missing:
        raise ValueError("missing required field(s): {}".format(", ".join(sorted(missing))))
    string_fields = EVENT_REQUIRED_FIELDS[str(event_name)] - {"qualified"}
    for field in string_fields | {"occurred_at", "source"}:
        if not isinstance(data[field], str) or not data[field].strip():
            raise ValueError("field {!r} must be a non-empty string".format(field))
    if event_name == "review_submitted" and not isinstance(data["qualified"], bool):
        raise ValueError("field 'qualified' must be bool")
    if "review_cycle" in data and (
        not isinstance(data["review_cycle"], str) or not data["review_cycle"].strip()
    ):
        raise ValueError("field 'review_cycle' must be a non-empty string")
    parse_timestamp(str(data["occurred_at"]))


def read_events(
    paths: List[Path],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    events: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            warnings.append(
                {"code": "BAD_EVENT_FILE", "file": str(path), "detail": str(exc)}
            )
            continue
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                warnings.append(
                    {
                        "code": "BAD_EVENT_JSON",
                        "file": str(path),
                        "line": line_number,
                        "detail": str(exc),
                    }
                )
                continue
            try:
                _validate_event(data)
            except (TypeError, ValueError) as exc:
                warnings.append(
                    {
                        "code": "BAD_EVENT_SCHEMA",
                        "file": str(path),
                        "line": line_number,
                        "detail": str(exc),
                    }
                )
                continue
            data["occurred_at"] = parse_timestamp(data["occurred_at"]).isoformat()
            events.append(data)
    return events, warnings


def read_check_snapshot(
    paths: List[Path], until: datetime
) -> Tuple[Optional[set], List[Dict[str, Any]]]:
    if not paths:
        return None, []

    events, warnings = read_events(paths)
    complete = not warnings
    fingerprints = set()
    for event in events:
        if event["event"] != "violation_observed":
            warnings.append(
                {
                    "code": "BAD_CHECK_SNAPSHOT",
                    "detail": "CHECK snapshots may contain only violation_observed records.",
                }
            )
            complete = False
            continue
        if _event_time(event) > until:
            warnings.append(
                {
                    "code": "BAD_CHECK_SNAPSHOT",
                    "detail": "CHECK snapshot contains an observation after --until.",
                }
            )
            complete = False
            continue
        fingerprints.add(str(event["fingerprint"]))

    return (fingerprints if complete else None), warnings


def _event_entity(event: Dict[str, Any]) -> str:
    if "fingerprint" in event:
        return str(event["fingerprint"])
    if event.get("event") in {"review_requested", "review_submitted"}:
        return "{}:{}:{}".format(
            event.get("adr_id"), event.get("review_cycle"), event.get("reviewer")
        )
    return str(event.get("adr_id"))


def _event_identity(event: Dict[str, Any]) -> Tuple[str, str, str]:
    return (
        str(event["event"]),
        parse_timestamp(str(event["occurred_at"])).isoformat(),
        _event_entity(event),
    )


def _event_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    payload = {key: value for key, value in event.items() if key != "source"}
    payload["occurred_at"] = parse_timestamp(str(event["occurred_at"])).isoformat()
    return payload


def merge_events(
    source_events: List[Tuple[str, List[Dict[str, Any]]]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    merged: Dict[Tuple[str, str, str], Tuple[str, Dict[str, Any]]] = {}
    warnings: List[Dict[str, Any]] = []
    for source_group, events in source_events:
        for event in events:
            identity = _event_identity(event)
            existing = merged.get(identity)
            if existing is None:
                merged[identity] = (source_group, event)
                continue
            kept_group, kept_event = existing
            if _event_payload(kept_event) == _event_payload(event):
                continue
            warnings.append(
                {
                    "code": "EVENT_CONFLICT",
                    "event": str(event["event"]),
                    "entity": _event_entity(event).split(":", 1)[0],
                    "kept_source": kept_group,
                    "discarded_source": source_group,
                }
            )

    ordered = sorted(
        (event for _, event in merged.values()),
        key=lambda event: (_event_time(event), str(event["event"]), _event_entity(event)),
    )
    return ordered, warnings


def _run_git(root: Path, arguments: List[str]) -> subprocess.CompletedProcess:
    command = ["git"] + arguments
    try:
        return subprocess.run(
            command,
            cwd=str(root),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return subprocess.CompletedProcess(command, 127, "", "")


def collect_git_events(
    root: Path, adr_dir: Path
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    probe = _run_git(root, ["rev-parse", "--is-inside-work-tree"])
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return [], [
            {"code": "GIT_UNAVAILABLE", "detail": "Root is not a Git work tree."}
        ]
    top_result = _run_git(root, ["rev-parse", "--show-toplevel"])
    if top_result.returncode != 0:
        return [], [
            {"code": "GIT_UNAVAILABLE", "detail": "Could not resolve Git top-level."}
        ]
    git_root = Path(top_result.stdout.strip()).resolve()

    events: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    for path in sorted(adr_dir.glob("[0-9]*.md")):
        try:
            relative_path = path.resolve().relative_to(git_root).as_posix()
        except ValueError:
            warnings.append(
                {
                    "code": "GIT_PATH_OUTSIDE_ROOT",
                    "file": str(path),
                    "detail": "ADR path is outside the Git root.",
                }
            )
            continue
        history = _run_git(
            git_root,
            ["log", "--follow", "--format=%H%x1f%aI", "--", relative_path],
        )
        if history.returncode != 0:
            warnings.append(
                {
                    "code": "GIT_HISTORY_FAILED",
                    "file": relative_path,
                    "detail": "Could not read ADR history.",
                }
            )
            continue

        versions_newest_first: List[Tuple[str, str, Dict[str, str]]] = []
        historical_path = relative_path
        for line in [item for item in history.stdout.splitlines() if item]:
            commit, separator, timestamp = line.partition("\x1f")
            if not separator:
                continue
            shown = _run_git(git_root, ["show", "{}:{}".format(commit, historical_path)])
            if shown.returncode != 0:
                warnings.append(
                    {
                        "code": "GIT_VERSION_UNAVAILABLE",
                        "file": relative_path,
                        "commit": commit,
                        "detail": "Could not read historical ADR content.",
                    }
                )
                continue
            try:
                data = _parse_scalar_frontmatter(shown.stdout)
                if not data.get("id") or not data.get("status"):
                    raise ValueError("historical ADR is missing id or status")
                occurred_at = parse_timestamp(timestamp).isoformat()
            except (TypeError, ValueError) as exc:
                warnings.append(
                    {
                        "code": "BAD_GIT_FRONTMATTER",
                        "file": relative_path,
                        "commit": commit,
                        "detail": str(exc),
                    }
                )
                continue
            versions_newest_first.append((commit, occurred_at, data))

            names = _run_git(
                git_root,
                ["diff-tree", "--no-commit-id", "--name-status", "-r", "-M", commit],
            )
            if names.returncode == 0:
                for changed_line in names.stdout.splitlines():
                    parts = changed_line.split("\t")
                    if len(parts) == 3 and parts[0].startswith("R"):
                        old_name, new_name = parts[1], parts[2]
                        if new_name == historical_path:
                            historical_path = old_name
                            break

        versions = list(reversed(versions_newest_first))

        previous_status = None
        previous_id = None
        for _, occurred_at, data in versions:
            adr_id = data["id"]
            status = data["status"]
            if previous_status is None:
                events.append(
                    {
                        "schema_version": 1,
                        "event": "adr_created",
                        "occurred_at": occurred_at,
                        "source": "git",
                        "adr_id": adr_id,
                        "status": status,
                    }
                )
            elif adr_id != previous_id:
                warnings.append(
                    {
                        "code": "ADR_ID_CHANGED",
                        "file": relative_path,
                        "detail": "ADR ID changed from {} to {}.".format(
                            previous_id, adr_id
                        ),
                    }
                )
            elif status != previous_status:
                events.append(
                    {
                        "schema_version": 1,
                        "event": "adr_status_changed",
                        "occurred_at": occurred_at,
                        "source": "git",
                        "adr_id": adr_id,
                        "from": previous_status,
                        "to": status,
                    }
                )
            previous_id = adr_id
            previous_status = status

    return sorted(events, key=_event_time), warnings


def _run_gh(root: Path, arguments: List[str]) -> subprocess.CompletedProcess:
    command = ["gh"] + arguments
    try:
        return subprocess.run(
            command,
            cwd=str(root),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return subprocess.CompletedProcess(command, 127, "", "")


def collect_github_payload(
    root: Path,
) -> Tuple[Any, List[Dict[str, str]]]:
    repository_result = _run_gh(root, ["repo", "view", "--json", "nameWithOwner"])
    if repository_result.returncode != 0:
        return None, [
            {
                "code": "GITHUB_UNAVAILABLE",
                "detail": "Could not determine the GitHub repository.",
            }
        ]
    try:
        repository_data = json.loads(repository_result.stdout)
        owner, name = str(repository_data["nameWithOwner"]).split("/", 1)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None, [
            {
                "code": "GITHUB_BAD_RESPONSE",
                "detail": "GitHub returned an invalid repository identity.",
            }
        ]

    all_nodes: List[Dict[str, Any]] = []
    cursor = None
    while True:
        arguments = [
            "api",
            "graphql",
            "-f",
            "query={}".format(GITHUB_REVIEW_QUERY),
            "-F",
            "owner={}".format(owner),
            "-F",
            "name={}".format(name),
        ]
        if cursor is not None:
            arguments += ["-F", "cursor={}".format(cursor)]
        result = _run_gh(root, arguments)
        if result.returncode != 0:
            return None, [
                {
                    "code": "GITHUB_UNAVAILABLE",
                    "detail": "Could not collect GitHub review history.",
                }
            ]
        try:
            page_payload = json.loads(result.stdout)
            pull_requests = page_payload["data"]["repository"]["pullRequests"]
            all_nodes.extend(pull_requests["nodes"])
            page_info = pull_requests["pageInfo"]
        except (json.JSONDecodeError, KeyError, TypeError):
            return None, [
                {
                    "code": "GITHUB_BAD_RESPONSE",
                    "detail": "GitHub returned invalid review JSON.",
                }
            ]
        if not page_info.get("hasNextPage"):
            pull_requests["nodes"] = all_nodes
            return page_payload, []
        cursor = page_info.get("endCursor")
        if not cursor:
            return None, [
                {
                    "code": "GITHUB_BAD_RESPONSE",
                    "detail": "GitHub pagination omitted its next cursor.",
                }
            ]


def _reviewer_login(node: Any) -> Any:
    if not isinstance(node, dict):
        return None
    return node.get("login") or node.get("slug")


def normalize_github_reviews(
    payload: Any, adr_paths: Dict[str, str]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    warnings: List[Dict[str, str]] = []
    try:
        pull_requests = payload["data"]["repository"]["pullRequests"]
        nodes = pull_requests["nodes"]
    except (KeyError, TypeError):
        return [], [
            {
                "code": "GITHUB_BAD_RESPONSE",
                "detail": "GitHub review response is missing pull request data.",
            }
        ]
    if pull_requests.get("pageInfo", {}).get("hasNextPage"):
        warnings.append(
            {
                "code": "GITHUB_RESULTS_TRUNCATED",
                "detail": "GitHub returned more pull requests than this collection fetched.",
            }
        )

    events: List[Dict[str, Any]] = []
    incomplete = False
    for pull_request in nodes:
        files = pull_request.get("files", {})
        timeline = pull_request.get("timelineItems", {})
        if files.get("pageInfo", {}).get("hasNextPage") or timeline.get(
            "pageInfo", {}
        ).get("hasNextPage"):
            incomplete = True
            warnings.append(
                {
                    "code": "GITHUB_PR_RESULTS_TRUNCATED",
                    "detail": "GitHub truncated files or review events for pull request {}.".format(
                        pull_request.get("number")
                    ),
                }
            )
            continue
        adr_ids = sorted(
            {
                adr_paths[file_node.get("path")]
                for file_node in files.get("nodes", [])
                if file_node.get("path") in adr_paths
            }
        )
        if not adr_ids:
            continue
        author = _reviewer_login(pull_request.get("author"))
        provider_cycle = str(pull_request.get("id") or pull_request.get("number"))
        review_cycle = hashlib.sha256(
            "github:{}".format(provider_cycle).encode("utf-8")
        ).hexdigest()[:16]
        requested = set()
        timeline_nodes = sorted(
            timeline.get("nodes", []),
            key=lambda node: str(node.get("createdAt") or node.get("submittedAt") or ""),
        )
        for node in timeline_nodes:
            if node.get("__typename") == "ReviewRequestedEvent":
                reviewer = _reviewer_login(node.get("requestedReviewer"))
                occurred_at = node.get("createdAt")
                if not reviewer or not occurred_at:
                    continue
                requested.add(reviewer)
                for adr_id in adr_ids:
                    events.append(
                        {
                            "schema_version": 1,
                            "event": "review_requested",
                            "occurred_at": parse_timestamp(str(occurred_at)).isoformat(),
                            "source": "github",
                            "adr_id": adr_id,
                            "reviewer": reviewer,
                            "review_cycle": review_cycle,
                        }
                    )
            elif node.get("__typename") == "PullRequestReview":
                reviewer = _reviewer_login(node.get("author"))
                occurred_at = node.get("submittedAt")
                if not reviewer or not occurred_at:
                    continue
                qualified = reviewer in requested and reviewer != author
                for adr_id in adr_ids:
                    events.append(
                        {
                            "schema_version": 1,
                            "event": "review_submitted",
                            "occurred_at": parse_timestamp(str(occurred_at)).isoformat(),
                            "source": "github",
                            "adr_id": adr_id,
                            "reviewer": reviewer,
                            "qualified": qualified,
                            "review_cycle": review_cycle,
                        }
                    )
    if incomplete:
        return [], warnings
    return sorted(events, key=_event_time), warnings


def _event_time(event: Dict[str, Any]) -> datetime:
    return parse_timestamp(str(event["occurred_at"]))


def _in_period(event: Dict[str, Any], since: datetime, until: datetime) -> bool:
    occurred_at = _event_time(event)
    return since <= occurred_at <= until


def _coverage(eligible: int, measured: int) -> Dict[str, Any]:
    ratio = measured / eligible if eligible else None
    return {"eligible": eligible, "measured": measured, "ratio": ratio}


def _decision_lead_time(
    adrs: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
    since: datetime,
    until: datetime,
) -> Dict[str, Any]:
    by_adr: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        if event.get("event") in {"adr_created", "adr_status_changed"}:
            by_adr.setdefault(str(event.get("adr_id")), []).append(event)

    eligible = 0
    durations: List[float] = []
    sources = set()
    for adr_events in by_adr.values():
        ordered = sorted(adr_events, key=_event_time)
        proposed_at = None
        outcome = None
        for event in ordered:
            status = event.get("status") if event["event"] == "adr_created" else event.get("to")
            if status == "proposed" and proposed_at is None:
                proposed_at = _event_time(event)
            if status in {"accepted", "rejected"}:
                outcome = event
                break
        if outcome is None or not _in_period(outcome, since, until):
            continue
        eligible += 1
        if proposed_at is not None and proposed_at <= _event_time(outcome):
            durations.append((_event_time(outcome) - proposed_at).total_seconds() / 3600)
            sources.update(
                str(event.get("source"))
                for event in ordered
                if proposed_at <= _event_time(event) <= _event_time(outcome)
            )

    terminal_event_adr_ids = {
        adr_id
        for adr_id, adr_events in by_adr.items()
        if any(
            (
                event.get("status")
                if event.get("event") == "adr_created"
                else event.get("to")
            )
            in {"accepted", "rejected"}
            for event in adr_events
        )
    }
    for adr in adrs:
        if str(adr.get("id")) in terminal_event_adr_ids:
            continue
        if adr.get("status") not in {"accepted", "rejected", "superseded"}:
            continue
        observed_at = parse_timestamp(str(adr.get("date")))
        if since <= observed_at <= until:
            eligible += 1

    result: Dict[str, Any] = {
        "available": bool(durations),
        "median_hours": statistics.median(durations) if durations else None,
        "sample_size": len(durations),
        "coverage": _coverage(eligible, len(durations)),
        "sources": sorted(sources),
    }
    if not durations:
        result["reason"] = "No completed decision had observable proposed history."
    return result


def _review_latency(
    events: List[Dict[str, Any]], since: datetime, until: datetime
) -> Dict[str, Any]:
    requests = [event for event in events if event.get("event") == "review_requested"]
    submissions = [event for event in events if event.get("event") == "review_submitted"]
    durations: List[float] = []
    open_cycles = 0
    sources = set()
    cycles: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for request in requests:
        adr_id = str(request.get("adr_id"))
        cycle_id = str(request.get("review_cycle") or adr_id)
        cycles.setdefault((adr_id, cycle_id), []).append(request)

    for (adr_id, cycle_id), cycle_requests in cycles.items():
        request = min(cycle_requests, key=_event_time)
        if _event_time(request) > until:
            continue
        candidates = [
            event
            for event in submissions
            if str(event.get("adr_id")) == adr_id
            and str(event.get("review_cycle") or adr_id) == cycle_id
            and event.get("qualified") is True
            and _event_time(event) >= _event_time(request)
            and _event_time(event) <= until
        ]
        if not candidates:
            open_cycles += 1
            sources.add(str(request.get("source")))
            continue
        submitted = min(candidates, key=_event_time)
        if _event_time(submitted) < since:
            continue
        durations.append(
            (_event_time(submitted) - _event_time(request)).total_seconds() / 3600
        )
        sources.update(str(item.get("source")) for item in cycle_requests)
        sources.add(str(submitted.get("source")))

    eligible = len(durations) + open_cycles
    result: Dict[str, Any] = {
        "available": bool(durations),
        "median_hours": statistics.median(durations) if durations else None,
        "sample_size": len(durations),
        "open_cycles": open_cycles,
        "coverage": _coverage(eligible, len(durations)),
        "sources": sorted(sources),
    }
    if not durations:
        result["reason"] = "No completed qualified review cycle was available."
    return result


def _supersession_rate(
    events: List[Dict[str, Any]], since: datetime, until: datetime
) -> Dict[str, Any]:
    lifecycle_events = [
        event
        for event in events
        if event.get("event") in {"adr_created", "adr_status_changed"}
        and _in_period(event, since, until)
    ]
    accepted_ids = {
        str(event.get("adr_id"))
        for event in lifecycle_events
        if event.get("to") == "accepted"
        or (event.get("event") == "adr_created" and event.get("status") == "accepted")
    }
    superseded_in_period = {
        str(event.get("adr_id"))
        for event in lifecycle_events
        if event.get("to") == "superseded"
    }
    superseded_ids = superseded_in_period & accepted_ids
    accepted = len(accepted_ids)
    superseded = len(superseded_ids)
    sources = sorted(
        {
            str(event.get("source"))
            for event in lifecycle_events
            if event.get("adr_id") in accepted_ids | superseded_ids
        }
    )
    result: Dict[str, Any] = {
        "available": accepted > 0,
        "rate": superseded / accepted if accepted else None,
        "superseded": superseded,
        "accepted": accepted,
        "sources": sources,
    }
    if not accepted:
        result["reason"] = "No accepted transitions were observed in the period."
    return result


def _unresolved_violations(
    events: List[Dict[str, Any]],
    until: datetime,
    current_snapshot: Optional[set] = None,
) -> Dict[str, Any]:
    violation_events = [
        event
        for event in events
        if event.get("event") in {"violation_observed", "violation_resolved"}
        and _event_time(event) <= until
    ]
    if not violation_events and current_snapshot is None:
        return {
            "available": False,
            "open_count": None,
            "age_available": False,
            "median_age_days": None,
            "max_age_days": None,
            "sources": [],
            "reason": "No CHECK violation observations were available.",
        }

    open_since: Dict[str, datetime] = {}
    sources = set()
    for event in sorted(violation_events, key=_event_time):
        fingerprint = str(event.get("fingerprint"))
        sources.add(str(event.get("source")))
        if event["event"] == "violation_resolved":
            open_since.pop(fingerprint, None)
        elif fingerprint not in open_since:
            open_since[fingerprint] = _event_time(event)

    if current_snapshot is not None:
        sources.add("check_results")
        if not current_snapshot:
            open_since = {}
        elif not current_snapshot.issubset(open_since):
            return {
                "available": True,
                "open_count": len(current_snapshot),
                "age_available": False,
                "median_age_days": None,
                "max_age_days": None,
                "sources": sorted(sources),
                "reason": "Some current violations lack historical first-observed evidence.",
            }
        open_since = {
            fingerprint: open_since[fingerprint] for fingerprint in current_snapshot
        }

    ages = [(until.date() - opened.date()).days for opened in open_since.values()]
    return {
        "available": True,
        "open_count": len(open_since),
        "age_available": True,
        "median_age_days": statistics.median(ages) if ages else None,
        "max_age_days": max(ages) if ages else None,
        "sources": sorted(sources),
    }


def _exception_age(
    exceptions: List[Dict[str, Any]], until: datetime
) -> Dict[str, Any]:
    ages: List[int] = []
    expired_count = 0
    for exception in exceptions:
        created = parse_timestamp(str(exception["created"])).date()
        expiry = parse_timestamp(str(exception["expiry"])).date()
        if created > until.date():
            continue
        if expiry < until.date():
            expired_count += 1
        else:
            ages.append((until.date() - created).days)
    return {
        "available": True,
        "active_count": len(ages),
        "median_age_days": statistics.median(ages) if ages else None,
        "max_age_days": max(ages) if ages else None,
        "expired_count": expired_count,
        "sources": ["exceptions"],
    }


def calculate_metrics(
    adrs: List[Dict[str, Any]],
    exceptions: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
    since: datetime,
    until: datetime,
    current_violation_fingerprints: Optional[set] = None,
) -> Dict[str, Any]:
    return {
        "decision_lead_time": _decision_lead_time(adrs, events, since, until),
        "review_latency": _review_latency(events, since, until),
        "supersession_rate": _supersession_rate(events, since, until),
        "unresolved_violations": _unresolved_violations(
            events, until, current_violation_fingerprints
        ),
        "exception_age": _exception_age(exceptions, until),
    }


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


if __name__ == "__main__":
    sys.exit(main())
