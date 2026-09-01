#!/usr/bin/env python3
"""Collect provider-neutral ADR adoption metrics as deterministic JSON."""

import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


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


def _event_time(event: Dict[str, Any]) -> datetime:
    return parse_timestamp(str(event["occurred_at"]))


def _in_period(event: Dict[str, Any], since: datetime, until: datetime) -> bool:
    occurred_at = _event_time(event)
    return since <= occurred_at <= until


def _coverage(eligible: int, measured: int) -> Dict[str, Any]:
    ratio = measured / eligible if eligible else None
    return {"eligible": eligible, "measured": measured, "ratio": ratio}


def _decision_lead_time(
    events: List[Dict[str, Any]], since: datetime, until: datetime
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
            if status in {"accepted", "rejected"} and _in_period(event, since, until):
                outcome = event
                break
        if outcome is None:
            continue
        eligible += 1
        if proposed_at is not None and proposed_at <= _event_time(outcome):
            durations.append((_event_time(outcome) - proposed_at).total_seconds() / 3600)
            sources.update(
                str(event.get("source"))
                for event in ordered
                if proposed_at <= _event_time(event) <= _event_time(outcome)
            )

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
    for request in sorted(requests, key=_event_time):
        if not (since <= _event_time(request) <= until):
            continue
        candidates = [
            event
            for event in submissions
            if event.get("adr_id") == request.get("adr_id")
            and event.get("qualified") is True
            and _event_time(event) >= _event_time(request)
            and _event_time(event) <= until
        ]
        if not candidates:
            open_cycles += 1
            sources.add(str(request.get("source")))
            continue
        submitted = min(candidates, key=_event_time)
        durations.append(
            (_event_time(submitted) - _event_time(request)).total_seconds() / 3600
        )
        sources.update((str(request.get("source")), str(submitted.get("source"))))

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
    transitions = [
        event
        for event in events
        if event.get("event") == "adr_status_changed" and _in_period(event, since, until)
    ]
    accepted = sum(event.get("to") == "accepted" for event in transitions)
    superseded = sum(event.get("to") == "superseded" for event in transitions)
    sources = sorted(
        {
            str(event.get("source"))
            for event in transitions
            if event.get("to") in {"accepted", "superseded"}
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
    events: List[Dict[str, Any]], until: datetime
) -> Dict[str, Any]:
    violation_events = [
        event
        for event in events
        if event.get("event") in {"violation_observed", "violation_resolved"}
        and _event_time(event) <= until
    ]
    if not violation_events:
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
) -> Dict[str, Any]:
    del adrs  # Current ADR snapshots are retained for future coverage extensions.
    return {
        "decision_lead_time": _decision_lead_time(events, since, until),
        "review_latency": _review_latency(events, since, until),
        "supersession_rate": _supersession_rate(events, since, until),
        "unresolved_violations": _unresolved_violations(events, until),
        "exception_age": _exception_age(exceptions, until),
    }
