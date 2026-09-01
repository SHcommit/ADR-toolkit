import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


_ADOPTION_METRICS_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "adoption_metrics.py"
)
_spec = importlib.util.spec_from_file_location(
    "_repo_root_adoption_metrics", _ADOPTION_METRICS_PATH
)
adoption_metrics = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adoption_metrics)

SINCE = datetime(2026, 1, 1, tzinfo=timezone.utc)
UNTIL = datetime(2026, 1, 31, tzinfo=timezone.utc)


def _event(event, occurred_at, source="events", **payload):
    return {
        "schema_version": 1,
        "event": event,
        "occurred_at": occurred_at,
        "source": source,
        **payload,
    }


def test_read_adrs_returns_valid_frontmatter_and_warns_for_malformed_file(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-a.md").write_text(
        "---\n"
        "id: ADR-0001\n"
        "title: A\n"
        "status: accepted\n"
        "date: 2026-01-02\n"
        "---\n"
        "Body\n",
        encoding="utf-8",
    )
    (adr_dir / "0002-b.md").write_text("not frontmatter\n", encoding="utf-8")

    records, warnings = adoption_metrics.read_adrs(adr_dir)

    assert records == [
        {
            "id": "ADR-0001",
            "title": "A",
            "status": "accepted",
            "date": "2026-01-02",
            "file": "0001-a.md",
        }
    ]
    assert warnings[0]["code"] == "BAD_FRONTMATTER"
    assert warnings[0]["file"] == "0002-b.md"


def test_read_exceptions_keeps_valid_records_and_warns_for_bad_json(tmp_path):
    exceptions_dir = tmp_path / "exceptions"
    exceptions_dir.mkdir()
    valid = {
        "id": "EXC-0001",
        "adr_id": "ADR-0001",
        "rule_id": "r1",
        "owner": "team",
        "reason": "migration",
        "scope": ["src/a.py"],
        "created": "2026-01-01",
        "expiry": "2026-01-10",
    }
    (exceptions_dir / "0001.json").write_text(json.dumps(valid), encoding="utf-8")
    (exceptions_dir / "0002.json").write_text("{", encoding="utf-8")

    records, warnings = adoption_metrics.read_exceptions(tmp_path)

    assert records == [valid]
    assert warnings[0]["code"] == "BAD_EXCEPTION"
    assert warnings[0]["file"] == "0002.json"


def test_decision_lead_time_is_median_completed_cycle_hours():
    events = [
        _event(
            "adr_created",
            "2026-01-01T00:00:00Z",
            adr_id="ADR-0001",
            status="proposed",
        ),
        _event(
            "adr_status_changed",
            "2026-01-02T00:00:00Z",
            adr_id="ADR-0001",
            **{"from": "proposed", "to": "accepted"},
        ),
        _event(
            "adr_created",
            "2026-01-01T00:00:00Z",
            adr_id="ADR-0002",
            status="proposed",
        ),
        _event(
            "adr_status_changed",
            "2026-01-04T00:00:00Z",
            adr_id="ADR-0002",
            **{"from": "proposed", "to": "rejected"},
        ),
    ]

    result = adoption_metrics.calculate_metrics([], [], events, SINCE, UNTIL)[
        "decision_lead_time"
    ]

    assert result == {
        "available": True,
        "median_hours": 48.0,
        "sample_size": 2,
        "coverage": {"eligible": 2, "measured": 2, "ratio": 1.0},
        "sources": ["events"],
    }


def test_decision_lead_time_excludes_terminal_first_observation_from_coverage():
    events = [
        _event(
            "adr_created",
            "2026-01-02T00:00:00Z",
            source="git",
            adr_id="ADR-0001",
            status="accepted",
        )
    ]

    result = adoption_metrics.calculate_metrics([], [], events, SINCE, UNTIL)[
        "decision_lead_time"
    ]

    assert result["available"] is False
    assert result["median_hours"] is None
    assert result["coverage"] == {"eligible": 1, "measured": 0, "ratio": 0.0}
    assert result["reason"] == "No completed decision had observable proposed history."


def test_review_latency_uses_first_qualified_review_after_request():
    events = [
        _event(
            "review_requested",
            "2026-01-01T00:00:00Z",
            adr_id="ADR-0001",
            reviewer="alice",
        ),
        _event(
            "review_submitted",
            "2026-01-01T01:00:00Z",
            adr_id="ADR-0001",
            reviewer="bob",
            qualified=False,
        ),
        _event(
            "review_submitted",
            "2026-01-01T06:00:00Z",
            adr_id="ADR-0001",
            reviewer="alice",
            qualified=True,
        ),
    ]

    result = adoption_metrics.calculate_metrics([], [], events, SINCE, UNTIL)[
        "review_latency"
    ]

    assert result["median_hours"] == 6.0
    assert result["sample_size"] == 1
    assert result["open_cycles"] == 0
    assert result["coverage"] == {"eligible": 1, "measured": 1, "ratio": 1.0}


def test_review_latency_reports_open_cycle_without_adding_it_to_median():
    events = [
        _event(
            "review_requested",
            "2026-01-01T00:00:00Z",
            adr_id="ADR-0001",
            reviewer="alice",
        ),
        _event(
            "review_requested",
            "2026-01-02T00:00:00Z",
            adr_id="ADR-0002",
            reviewer="bob",
        ),
        _event(
            "review_submitted",
            "2026-01-02T12:00:00Z",
            adr_id="ADR-0002",
            reviewer="bob",
            qualified=True,
        ),
    ]

    result = adoption_metrics.calculate_metrics([], [], events, SINCE, UNTIL)[
        "review_latency"
    ]

    assert result["median_hours"] == 12.0
    assert result["open_cycles"] == 1
    assert result["coverage"] == {"eligible": 2, "measured": 1, "ratio": 0.5}


def test_supersession_rate_uses_transitions_within_period():
    events = [
        _event(
            "adr_status_changed",
            "2026-01-02T00:00:00Z",
            adr_id="ADR-0001",
            **{"from": "proposed", "to": "accepted"},
        ),
        _event(
            "adr_status_changed",
            "2026-01-03T00:00:00Z",
            adr_id="ADR-0002",
            **{"from": "proposed", "to": "accepted"},
        ),
        _event(
            "adr_status_changed",
            "2026-01-04T00:00:00Z",
            adr_id="ADR-0001",
            **{"from": "accepted", "to": "superseded"},
        ),
        _event(
            "adr_status_changed",
            "2025-12-31T00:00:00Z",
            adr_id="ADR-0003",
            **{"from": "accepted", "to": "superseded"},
        ),
    ]

    result = adoption_metrics.calculate_metrics([], [], events, SINCE, UNTIL)[
        "supersession_rate"
    ]

    assert result == {
        "available": True,
        "rate": 0.5,
        "superseded": 1,
        "accepted": 2,
        "sources": ["events"],
    }


def test_supersession_rate_is_unavailable_when_no_acceptance_is_observed():
    result = adoption_metrics.calculate_metrics([], [], [], SINCE, UNTIL)[
        "supersession_rate"
    ]

    assert result["available"] is False
    assert result["rate"] is None
    assert result["accepted"] == 0
    assert result["reason"] == "No accepted transitions were observed in the period."


def test_unresolved_violations_use_first_observation_after_latest_resolution():
    events = [
        _event(
            "violation_observed",
            "2026-01-01T00:00:00Z",
            fingerprint="f1",
            adr_id="ADR-0001",
            rule_id="r1",
        ),
        _event(
            "violation_resolved",
            "2026-01-05T00:00:00Z",
            fingerprint="f1",
            adr_id="ADR-0001",
            rule_id="r1",
        ),
        _event(
            "violation_observed",
            "2026-01-21T00:00:00Z",
            fingerprint="f1",
            adr_id="ADR-0001",
            rule_id="r1",
        ),
    ]

    result = adoption_metrics.calculate_metrics([], [], events, SINCE, UNTIL)[
        "unresolved_violations"
    ]

    assert result == {
        "available": True,
        "open_count": 1,
        "age_available": True,
        "median_age_days": 10,
        "max_age_days": 10,
        "sources": ["events"],
    }


def test_unresolved_violations_are_unavailable_without_observations():
    result = adoption_metrics.calculate_metrics([], [], [], SINCE, UNTIL)[
        "unresolved_violations"
    ]

    assert result["available"] is False
    assert result["open_count"] is None
    assert result["reason"] == "No CHECK violation observations were available."


def test_exception_age_separates_active_age_from_expired_count():
    exceptions = [
        {"id": "EXC-0001", "created": "2026-01-01", "expiry": "2026-02-01"},
        {"id": "EXC-0002", "created": "2026-01-11", "expiry": "2026-02-02"},
        {"id": "EXC-0003", "created": "2026-01-01", "expiry": "2026-01-02"},
    ]

    result = adoption_metrics.calculate_metrics([], exceptions, [], SINCE, UNTIL)[
        "exception_age"
    ]

    assert result == {
        "available": True,
        "active_count": 2,
        "median_age_days": 25.0,
        "max_age_days": 30,
        "expired_count": 1,
        "sources": ["exceptions"],
    }


def test_exception_age_is_available_for_an_empty_exception_directory():
    result = adoption_metrics.calculate_metrics([], [], [], SINCE, UNTIL)[
        "exception_age"
    ]

    assert result["available"] is True
    assert result["active_count"] == 0
    assert result["median_age_days"] is None
    assert result["expired_count"] == 0
