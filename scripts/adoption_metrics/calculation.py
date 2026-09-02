"""Calculate provider-neutral ADR adoption metrics from collected inputs."""

import statistics
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .common import parse_timestamp

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

