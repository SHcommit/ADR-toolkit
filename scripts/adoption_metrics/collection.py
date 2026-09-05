"""Collect ADR, exception, event, Git, and GitHub adoption metric inputs."""

import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .common import parse_timestamp
from .constants import (
    ADR_ID_RE,
    DATE_ONLY_RE,
    EVENT_REQUIRED_FIELDS,
    EXCEPTION_FIELD_TYPES,
    EXCEPTION_ID_RE,
    FRONTMATTER_RE,
    GITHUB_REVIEW_QUERY,
    REQUIRED_EXCEPTION_FIELDS,
)

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


def _event_time(event: Dict[str, Any]) -> datetime:
    return parse_timestamp(str(event["occurred_at"]))


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
