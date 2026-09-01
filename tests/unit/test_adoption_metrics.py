import importlib.util
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest


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


def _git(repo, *args, timestamp=None):
    env = os.environ.copy()
    if timestamp is not None:
        env["GIT_AUTHOR_DATE"] = timestamp
        env["GIT_COMMITTER_DATE"] = timestamp
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )


def _write_adr(path, adr_id, status, date="2026-01-01"):
    path.write_text(
        "---\n"
        "id: {}\n".format(adr_id)
        + "title: Test decision\n"
        + "status: {}\n".format(status)
        + "date: {}\n".format(date)
        + "---\nBody\n",
        encoding="utf-8",
    )


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


def test_read_adrs_warns_and_skips_an_invalid_date(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _write_adr(adr_dir / "0001-test.md", "ADR-0001", "accepted", date="not-a-date")

    records, warnings = adoption_metrics.read_adrs(adr_dir)

    assert records == []
    assert warnings[0]["code"] == "BAD_FRONTMATTER"
    assert "date" in warnings[0]["detail"]


def test_read_exceptions_warns_and_skips_an_invalid_expiry(tmp_path):
    exceptions_dir = tmp_path / "exceptions"
    exceptions_dir.mkdir()
    invalid = {
        "id": "EXC-0001",
        "adr_id": "ADR-0001",
        "rule_id": "r1",
        "owner": "team",
        "reason": "migration",
        "scope": ["src/a.py"],
        "created": "2026-01-01",
        "expiry": "not-a-date",
    }
    (exceptions_dir / "0001.json").write_text(json.dumps(invalid), encoding="utf-8")

    records, warnings = adoption_metrics.read_exceptions(tmp_path)

    assert records == []
    assert warnings[0]["code"] == "BAD_EXCEPTION"
    assert "expiry" in warnings[0]["detail"]


def test_read_exceptions_rejects_wrong_types_and_invalid_ids(tmp_path):
    exceptions_dir = tmp_path / "exceptions"
    exceptions_dir.mkdir()
    invalid = {
        "id": "bad-id",
        "adr_id": "bad-adr",
        "rule_id": ["r1"],
        "owner": ["team"],
        "reason": "migration",
        "scope": "src/a.py",
        "created": "2026-01-01",
        "expiry": "2026-02-01",
    }
    (exceptions_dir / "0001.json").write_text(json.dumps(invalid), encoding="utf-8")

    records, warnings = adoption_metrics.read_exceptions(tmp_path)

    assert records == []
    assert warnings[0]["code"] == "BAD_EXCEPTION"


def test_read_exceptions_rejects_non_string_scope_and_timestamp_dates(tmp_path):
    exceptions_dir = tmp_path / "exceptions"
    exceptions_dir.mkdir()
    invalid = {
        "id": "EXC-0001",
        "adr_id": "ADR-0001",
        "rule_id": "r1",
        "owner": "team",
        "reason": "migration",
        "scope": [123],
        "created": "2026-01-01T12:00:00Z",
        "expiry": "2026-02-01",
    }
    (exceptions_dir / "0001.json").write_text(json.dumps(invalid), encoding="utf-8")

    records, warnings = adoption_metrics.read_exceptions(tmp_path)

    assert records == []
    assert warnings[0]["code"] == "BAD_EXCEPTION"


def test_exception_created_after_report_date_is_not_counted_as_negative_age():
    exceptions = [
        {"id": "EXC-0001", "created": "2026-02-01", "expiry": "2026-03-01"}
    ]

    result = adoption_metrics.calculate_metrics([], exceptions, [], SINCE, UNTIL)[
        "exception_age"
    ]

    assert result["active_count"] == 0
    assert result["expired_count"] == 0


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


def test_decision_lead_time_uses_current_terminal_adrs_for_coverage_without_history():
    adrs = [
        {
            "id": "ADR-0001",
            "title": "A",
            "status": "accepted",
            "date": "2026-01-02",
            "file": "0001-a.md",
        }
    ]

    result = adoption_metrics.calculate_metrics(adrs, [], [], SINCE, UNTIL)[
        "decision_lead_time"
    ]

    assert result["coverage"] == {"eligible": 1, "measured": 0, "ratio": 0.0}


def test_decision_lead_time_does_not_replace_pre_period_first_outcome():
    events = [
        _event(
            "adr_created",
            "2025-12-01T00:00:00Z",
            adr_id="ADR-0001",
            status="proposed",
        ),
        _event(
            "adr_status_changed",
            "2025-12-02T00:00:00Z",
            adr_id="ADR-0001",
            **{"from": "proposed", "to": "accepted"},
        ),
        _event(
            "adr_status_changed",
            "2026-01-02T00:00:00Z",
            adr_id="ADR-0001",
            **{"from": "deprecated", "to": "accepted"},
        ),
    ]

    result = adoption_metrics.calculate_metrics([], [], events, SINCE, UNTIL)[
        "decision_lead_time"
    ]

    assert result["coverage"] == {"eligible": 0, "measured": 0, "ratio": None}


def test_decision_lead_time_uses_snapshot_fallback_after_only_proposed_event():
    adrs = [{"id": "ADR-0001", "status": "accepted", "date": "2026-01-02"}]
    events = [
        _event(
            "adr_created",
            "2026-01-01T00:00:00Z",
            adr_id="ADR-0001",
            status="proposed",
        )
    ]

    result = adoption_metrics.calculate_metrics(adrs, [], events, SINCE, UNTIL)[
        "decision_lead_time"
    ]

    assert result["coverage"] == {"eligible": 1, "measured": 0, "ratio": 0.0}


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


def test_review_latency_filters_completed_cycles_by_submission_time():
    events = [
        _event(
            "review_requested",
            "2026-01-09T00:00:00Z",
            adr_id="ADR-0001",
            reviewer="alice",
            review_cycle="pr-7",
        ),
        _event(
            "review_submitted",
            "2026-01-11T00:00:00Z",
            adr_id="ADR-0001",
            reviewer="alice",
            qualified=True,
            review_cycle="pr-7",
        ),
    ]

    result = adoption_metrics.calculate_metrics(
        [],
        [],
        events,
        datetime(2026, 1, 10, tzinfo=timezone.utc),
        UNTIL,
    )["review_latency"]

    assert result["sample_size"] == 1
    assert result["median_hours"] == 48.0


def test_review_latency_groups_multiple_requested_reviewers_into_one_cycle():
    events = [
        _event(
            "review_requested",
            "2026-01-01T00:00:00Z",
            adr_id="ADR-0001",
            reviewer="alice",
            review_cycle="pr-7",
        ),
        _event(
            "review_requested",
            "2026-01-01T01:00:00Z",
            adr_id="ADR-0001",
            reviewer="bob",
            review_cycle="pr-7",
        ),
        _event(
            "review_submitted",
            "2026-01-01T06:00:00Z",
            adr_id="ADR-0001",
            reviewer="bob",
            qualified=True,
            review_cycle="pr-7",
        ),
    ]

    result = adoption_metrics.calculate_metrics([], [], events, SINCE, UNTIL)[
        "review_latency"
    ]

    assert result["sample_size"] == 1
    assert result["median_hours"] == 6.0
    assert result["coverage"] == {"eligible": 1, "measured": 1, "ratio": 1.0}


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


def test_supersession_rate_counts_an_adr_first_observed_as_accepted():
    events = [
        _event(
            "adr_created",
            "2026-01-02T00:00:00Z",
            source="git",
            adr_id="ADR-0001",
            status="accepted",
        ),
        _event(
            "adr_status_changed",
            "2026-01-03T00:00:00Z",
            source="git",
            adr_id="ADR-0001",
            **{"from": "accepted", "to": "superseded"},
        ),
    ]

    result = adoption_metrics.calculate_metrics([], [], events, SINCE, UNTIL)[
        "supersession_rate"
    ]

    assert result["available"] is True
    assert result["accepted"] == 1
    assert result["superseded"] == 1
    assert result["rate"] == 1.0


def test_supersession_rate_excludes_supersessions_outside_period_accepted_cohort():
    events = [
        _event(
            "adr_created",
            "2025-12-01T00:00:00Z",
            adr_id="ADR-OLD-1",
            status="accepted",
        ),
        _event(
            "adr_created",
            "2025-12-02T00:00:00Z",
            adr_id="ADR-OLD-2",
            status="accepted",
        ),
        _event(
            "adr_created",
            "2026-01-02T00:00:00Z",
            adr_id="ADR-NEW",
            status="accepted",
        ),
        _event(
            "adr_status_changed",
            "2026-01-03T00:00:00Z",
            adr_id="ADR-OLD-1",
            **{"from": "accepted", "to": "superseded"},
        ),
        _event(
            "adr_status_changed",
            "2026-01-04T00:00:00Z",
            adr_id="ADR-OLD-2",
            **{"from": "accepted", "to": "superseded"},
        ),
    ]

    result = adoption_metrics.calculate_metrics([], [], events, SINCE, UNTIL)[
        "supersession_rate"
    ]

    assert result["accepted"] == 1
    assert result["superseded"] == 0
    assert result["rate"] == 0.0


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


def test_read_events_keeps_valid_lines_and_warns_for_invalid_records(tmp_path):
    events_path = tmp_path / "events.jsonl"
    events_path.write_text(
        json.dumps(
            _event(
                "adr_created",
                "2026-01-01T00:00:00Z",
                adr_id="ADR-0001",
                status="proposed",
            )
        )
        + "\n"
        + "{\n"
        + json.dumps(
            {
                "schema_version": 2,
                "event": "adr_created",
                "occurred_at": "2026-01-01T00:00:00Z",
                "source": "events",
                "adr_id": "ADR-0002",
                "status": "accepted",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    events, warnings = adoption_metrics.read_events([events_path])

    assert len(events) == 1
    assert events[0]["adr_id"] == "ADR-0001"
    assert [warning["code"] for warning in warnings] == [
        "BAD_EVENT_JSON",
        "BAD_EVENT_SCHEMA",
    ]
    assert [warning["line"] for warning in warnings] == [2, 3]


def test_read_events_rejects_unknown_event_and_missing_required_payload(tmp_path):
    events_path = tmp_path / "events.jsonl"
    events_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "event": "unknown",
                "occurred_at": "2026-01-01T00:00:00Z",
                "source": "events",
            }
        )
        + "\n"
        + json.dumps(
            {
                "schema_version": 1,
                "event": "review_requested",
                "occurred_at": "2026-01-01T00:00:00Z",
                "source": "events",
                "adr_id": "ADR-0001",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    events, warnings = adoption_metrics.read_events([events_path])

    assert events == []
    assert [warning["code"] for warning in warnings] == [
        "BAD_EVENT_SCHEMA",
        "BAD_EVENT_SCHEMA",
    ]


def test_read_events_rejects_wrong_payload_types(tmp_path):
    events_path = tmp_path / "events.jsonl"
    events_path.write_text(
        json.dumps(
            _event(
                "review_submitted",
                "2026-01-01T00:00:00Z",
                adr_id="ADR-0001",
                reviewer="alice",
                qualified="yes",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    events, warnings = adoption_metrics.read_events([events_path])

    assert events == []
    assert warnings[0]["code"] == "BAD_EVENT_SCHEMA"


def test_read_events_requires_review_cycle_for_review_events(tmp_path):
    events_path = tmp_path / "events.jsonl"
    events_path.write_text(
        json.dumps(
            _event(
                "review_requested",
                "2026-01-01T00:00:00Z",
                adr_id="ADR-0001",
                reviewer="alice",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    events, warnings = adoption_metrics.read_events([events_path])

    assert events == []
    assert warnings[0]["code"] == "BAD_EVENT_SCHEMA"


def test_merge_events_treats_equivalent_utc_timestamp_spellings_as_duplicates():
    explicit = _event(
        "adr_created",
        "2026-01-01T00:00:00Z",
        adr_id="ADR-0001",
        status="accepted",
    )
    reconstructed = dict(
        explicit, occurred_at="2026-01-01T00:00:00+00:00", source="git"
    )

    events, warnings = adoption_metrics.merge_events(
        [("events", [explicit]), ("git", [reconstructed])]
    )

    assert len(events) == 1
    assert warnings == []


def test_merge_events_deduplicates_and_prefers_explicit_conflicting_payload():
    explicit = _event(
        "adr_created",
        "2026-01-01T00:00:00Z",
        source="manual_export",
        adr_id="ADR-0001",
        status="proposed",
    )
    reconstructed_duplicate = dict(explicit, source="git")
    reconstructed_conflict = dict(explicit, source="git", status="accepted")

    events, warnings = adoption_metrics.merge_events(
        [("events", [explicit]), ("git", [reconstructed_duplicate, reconstructed_conflict])]
    )

    assert events == [explicit]
    assert warnings == [
        {
            "code": "EVENT_CONFLICT",
            "event": "adr_created",
            "entity": "ADR-0001",
            "kept_source": "events",
            "discarded_source": "git",
        }
    ]


def test_collect_git_events_reconstructs_proposed_to_accepted_in_path_with_spaces(
    tmp_path,
):
    root = tmp_path / "repo with spaces"
    adr_dir = root / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _git(root, "init")
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "user.email", "test@example.com")
    adr_path = adr_dir / "0001-test.md"
    _write_adr(adr_path, "ADR-0001", "proposed")
    _git(root, "add", str(adr_path.relative_to(root)))
    _git(root, "commit", "-m", "propose", timestamp="2026-01-01T00:00:00Z")
    _write_adr(adr_path, "ADR-0001", "accepted")
    _git(root, "add", str(adr_path.relative_to(root)))
    _git(root, "commit", "-m", "accept", timestamp="2026-01-02T00:00:00Z")

    events, warnings = adoption_metrics.collect_git_events(root, adr_dir)

    assert warnings == []
    assert events == [
        _event(
            "adr_created",
            "2026-01-01T00:00:00+00:00",
            source="git",
            adr_id="ADR-0001",
            status="proposed",
        ),
        _event(
            "adr_status_changed",
            "2026-01-02T00:00:00+00:00",
            source="git",
            adr_id="ADR-0001",
            **{"from": "proposed", "to": "accepted"},
        ),
    ]


def test_collect_git_events_does_not_invent_proposed_for_terminal_first_commit(tmp_path):
    root = tmp_path / "repo"
    adr_dir = root / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _git(root, "init")
    _git(root, "config", "user.name", "Test")
    _git(root, "config", "user.email", "test@example.com")
    adr_path = adr_dir / "0001-test.md"
    _write_adr(adr_path, "ADR-0001", "accepted")
    _git(root, "add", str(adr_path.relative_to(root)))
    _git(root, "commit", "-m", "record", timestamp="2026-01-01T00:00:00Z")

    events, warnings = adoption_metrics.collect_git_events(root, adr_dir)

    assert warnings == []
    assert [event["status"] for event in events if event["event"] == "adr_created"] == [
        "accepted"
    ]
    assert not any(
        event.get("status") == "proposed" or event.get("to") == "proposed"
        for event in events
    )


def test_collect_git_events_follows_rename_inside_a_nested_project_root(tmp_path):
    repository = tmp_path / "repository"
    root = repository / "nested-project"
    adr_dir = root / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _git(repository, "init")
    _git(repository, "config", "user.name", "Test")
    _git(repository, "config", "user.email", "test@example.com")
    old_path = adr_dir / "0001-old.md"
    new_path = adr_dir / "0001-new.md"
    _write_adr(old_path, "ADR-0001", "proposed")
    _git(repository, "add", str(old_path.relative_to(repository)))
    _git(repository, "commit", "-m", "propose", timestamp="2026-01-01T00:00:00Z")
    _git(repository, "mv", str(old_path.relative_to(repository)), str(new_path.relative_to(repository)))
    _write_adr(new_path, "ADR-0001", "accepted")
    _git(repository, "add", str(new_path.relative_to(repository)))
    _git(repository, "commit", "-m", "rename and accept", timestamp="2026-01-02T00:00:00Z")

    events, warnings = adoption_metrics.collect_git_events(root, adr_dir)

    assert warnings == []
    assert [(event["event"], event.get("status"), event.get("to")) for event in events] == [
        ("adr_created", "proposed", None),
        ("adr_status_changed", None, "accepted"),
    ]


def test_github_adr_paths_are_relative_to_git_top_level_for_nested_root(tmp_path):
    repository = tmp_path / "repository"
    root = repository / "nested-project"
    adr_dir = root / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _git(repository, "init")

    paths = adoption_metrics.github_adr_paths(
        root, adr_dir, [{"id": "ADR-0001", "file": "0001-test.md"}]
    )

    assert paths == {
        "nested-project/docs/decisions/0001-test.md": "ADR-0001"
    }


def test_collect_git_events_degrades_cleanly_outside_a_git_repository(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)

    events, warnings = adoption_metrics.collect_git_events(tmp_path, adr_dir)

    assert events == []
    assert warnings == [
        {
            "code": "GIT_UNAVAILABLE",
            "detail": "Root is not a Git work tree.",
        }
    ]


def test_collect_git_events_degrades_when_git_executable_is_missing(tmp_path, monkeypatch):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)

    def missing_executable(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(adoption_metrics.subprocess, "run", missing_executable)

    events, warnings = adoption_metrics.collect_git_events(tmp_path, adr_dir)

    assert events == []
    assert warnings[0]["code"] == "GIT_UNAVAILABLE"


def test_normalize_github_reviews_qualifies_requested_non_author_reviewer():
    payload = {
        "data": {
            "repository": {
                "pullRequests": {
                    "nodes": [
                        {
                            "number": 7,
                            "id": "PR_node_opaque_7",
                            "author": {"login": "owner"},
                            "files": {
                                "nodes": [
                                    {"path": "docs/decisions/0001-test.md"},
                                    {"path": "src/app.py"},
                                ]
                            },
                            "timelineItems": {
                                "nodes": [
                                    {
                                        "__typename": "ReviewRequestedEvent",
                                        "createdAt": "2026-01-01T00:00:00Z",
                                        "requestedReviewer": {
                                            "__typename": "User",
                                            "login": "alice",
                                        },
                                    },
                                    {
                                        "__typename": "PullRequestReview",
                                        "submittedAt": "2026-01-01T01:00:00Z",
                                        "author": {"login": "bob"},
                                    },
                                    {
                                        "__typename": "PullRequestReview",
                                        "submittedAt": "2026-01-01T02:00:00Z",
                                        "author": {"login": "owner"},
                                    },
                                    {
                                        "__typename": "PullRequestReview",
                                        "submittedAt": "2026-01-01T03:00:00Z",
                                        "author": {"login": "alice"},
                                    },
                                ]
                            },
                        }
                    ],
                    "pageInfo": {"hasNextPage": False},
                }
            }
        }
    }

    events, warnings = adoption_metrics.normalize_github_reviews(
        payload, {"docs/decisions/0001-test.md": "ADR-0001"}
    )

    assert warnings == []
    submitted = [event for event in events if event["event"] == "review_submitted"]
    assert [(event["reviewer"], event["qualified"]) for event in submitted] == [
        ("bob", False),
        ("owner", False),
        ("alice", True),
    ]
    assert all(event["adr_id"] == "ADR-0001" for event in events)
    assert all(event["review_cycle"] != "github-pr-7" for event in events)


def test_normalize_github_reviews_warns_when_provider_result_is_truncated():
    payload = {
        "data": {
            "repository": {
                "pullRequests": {
                    "nodes": [],
                    "pageInfo": {"hasNextPage": True},
                }
            }
        }
    }

    events, warnings = adoption_metrics.normalize_github_reviews(payload, {})

    assert events == []
    assert warnings == [
        {
            "code": "GITHUB_RESULTS_TRUNCATED",
            "detail": "GitHub returned more pull requests than this collection fetched.",
        }
    ]


def test_collect_github_payload_hides_provider_stderr_on_failure(tmp_path, monkeypatch):
    def fail_gh(root, arguments):
        return subprocess.CompletedProcess(
            ["gh", *arguments], returncode=1, stdout="", stderr="token=secret-value"
        )

    monkeypatch.setattr(adoption_metrics, "_run_gh", fail_gh)

    payload, warnings = adoption_metrics.collect_github_payload(tmp_path)

    assert payload is None
    assert warnings == [
        {
            "code": "GITHUB_UNAVAILABLE",
            "detail": "Could not determine the GitHub repository.",
        }
    ]
    assert "secret-value" not in json.dumps(warnings)


def test_collect_github_payload_degrades_when_gh_executable_is_missing(
    tmp_path, monkeypatch
):
    def missing_executable(*args, **kwargs):
        raise FileNotFoundError("gh")

    monkeypatch.setattr(adoption_metrics.subprocess, "run", missing_executable)

    payload, warnings = adoption_metrics.collect_github_payload(tmp_path)

    assert payload is None
    assert warnings[0]["code"] == "GITHUB_UNAVAILABLE"


def test_collect_github_payload_paginates_until_all_pull_requests_are_loaded(
    tmp_path, monkeypatch
):
    first_page = {
        "data": {
            "repository": {
                "pullRequests": {
                    "nodes": [{"number": 1}],
                    "pageInfo": {"hasNextPage": True, "endCursor": "CURSOR-1"},
                }
            }
        }
    }
    second_page = {
        "data": {
            "repository": {
                "pullRequests": {
                    "nodes": [{"number": 2}],
                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                }
            }
        }
    }

    def fake_gh(root, arguments):
        if arguments[:2] == ["repo", "view"]:
            stdout = json.dumps({"nameWithOwner": "owner/repo"})
        elif any(value == "cursor=CURSOR-1" for value in arguments):
            stdout = json.dumps(second_page)
        else:
            query_argument = next(value for value in arguments if value.startswith("query="))
            assert "pageInfo { hasNextPage endCursor }" in query_argument
            stdout = json.dumps(first_page)
        return subprocess.CompletedProcess(["gh", *arguments], 0, stdout, "")

    monkeypatch.setattr(adoption_metrics, "_run_gh", fake_gh)

    payload, warnings = adoption_metrics.collect_github_payload(tmp_path)

    nodes = payload["data"]["repository"]["pullRequests"]["nodes"]
    assert [node["number"] for node in nodes] == [1, 2]
    assert warnings == []


def test_cli_emits_one_json_report_and_degrades_without_optional_history(tmp_path, capsys):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _write_adr(adr_dir / "0001-test.md", "ADR-0001", "accepted")

    return_code = adoption_metrics.main(
        [
            "--root",
            str(tmp_path),
            "--dir",
            "docs/decisions",
            "--until",
            "2026-01-31",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert return_code == 0
    assert captured.err == ""
    assert result["ok"] is True
    assert result["operation"] == "adoption_metrics"
    assert result["schema_version"] == 1
    assert result["period"] == {"since": "2026-01-01", "until": "2026-01-31"}
    assert set(result["metrics"]) == {
        "decision_lead_time",
        "review_latency",
        "supersession_rate",
        "unresolved_violations",
        "exception_age",
    }
    assert result["metrics"]["decision_lead_time"]["available"] is False
    assert result["metrics"]["exception_age"]["available"] is True
    assert [warning["code"] for warning in result["warnings"]] == ["GIT_UNAVAILABLE"]


def test_cli_uses_explicit_events_to_calculate_lead_time(tmp_path, capsys):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _write_adr(adr_dir / "0001-test.md", "ADR-0001", "accepted")
    events_path = tmp_path / "events.jsonl"
    events_path.write_text(
        json.dumps(
            _event(
                "adr_created",
                "2026-01-01T00:00:00Z",
                adr_id="ADR-0001",
                status="proposed",
            )
        )
        + "\n"
        + json.dumps(
            _event(
                "adr_status_changed",
                "2026-01-02T00:00:00Z",
                adr_id="ADR-0001",
                **{"from": "proposed", "to": "accepted"},
            )
        )
        + "\n",
        encoding="utf-8",
    )

    return_code = adoption_metrics.main(
        [
            "--root",
            str(tmp_path),
            "--dir",
            "docs/decisions",
            "--since",
            "2026-01-01",
            "--until",
            "2026-01-31",
            "--events",
            "events.jsonl",
            "--json",
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert return_code == 0
    assert result["metrics"]["decision_lead_time"]["median_hours"] == 24.0
    assert result["metrics"]["decision_lead_time"]["sources"] == ["events"]


def test_cli_current_check_results_report_count_without_inventing_age(tmp_path, capsys):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _write_adr(adr_dir / "0001-test.md", "ADR-0001", "accepted")
    check_path = tmp_path / "check.jsonl"
    check_path.write_text(
        json.dumps(
            _event(
                "violation_observed",
                "2026-01-31T00:00:00Z",
                adr_id="ADR-0001",
                rule_id="r1",
                fingerprint="ADR-0001:r1:src/a.py",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    return_code = adoption_metrics.main(
        [
            "--root",
            str(tmp_path),
            "--dir",
            "docs/decisions",
            "--until",
            "2026-01-31",
            "--check-results",
            "check.jsonl",
            "--json",
        ]
    )

    result = json.loads(capsys.readouterr().out)
    violations = result["metrics"]["unresolved_violations"]
    assert return_code == 0
    assert violations["open_count"] == 1
    assert violations["age_available"] is False
    assert violations["median_age_days"] is None
    assert violations["sources"] == ["check_results"]


def test_cli_empty_current_check_snapshot_reports_zero_and_closes_stale_history(
    tmp_path, capsys
):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _write_adr(adr_dir / "0001-test.md", "ADR-0001", "accepted")
    history_path = tmp_path / "events.jsonl"
    history_path.write_text(
        json.dumps(
            _event(
                "violation_observed",
                "2026-01-01T00:00:00Z",
                adr_id="ADR-0001",
                rule_id="r1",
                fingerprint="f1",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    check_path = tmp_path / "check.jsonl"
    check_path.write_text("", encoding="utf-8")

    return_code = adoption_metrics.main(
        [
            "--root",
            str(tmp_path),
            "--dir",
            "docs/decisions",
            "--until",
            "2026-01-31",
            "--events",
            "events.jsonl",
            "--check-results",
            "check.jsonl",
            "--json",
        ]
    )

    violations = json.loads(capsys.readouterr().out)["metrics"]["unresolved_violations"]
    assert return_code == 0
    assert violations["available"] is True
    assert violations["open_count"] == 0


@pytest.mark.parametrize("snapshot_contents", ["{not-json}\n", None])
def test_cli_invalid_check_snapshot_does_not_clear_stale_history(
    tmp_path, capsys, snapshot_contents
):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _write_adr(adr_dir / "0001-test.md", "ADR-0001", "accepted")
    history_path = tmp_path / "events.jsonl"
    history_path.write_text(
        json.dumps(
            _event(
                "violation_observed",
                "2026-01-01T00:00:00Z",
                adr_id="ADR-0001",
                rule_id="r1",
                fingerprint="f1",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    check_path = tmp_path / "check.jsonl"
    if snapshot_contents is not None:
        check_path.write_text(snapshot_contents, encoding="utf-8")

    return_code = adoption_metrics.main(
        [
            "--root",
            str(tmp_path),
            "--dir",
            "docs/decisions",
            "--until",
            "2026-01-31",
            "--events",
            "events.jsonl",
            "--check-results",
            "check.jsonl",
            "--json",
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert return_code == 0
    assert result["metrics"]["unresolved_violations"]["open_count"] == 1


def test_cli_non_violation_check_record_does_not_clear_stale_history(tmp_path, capsys):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _write_adr(adr_dir / "0001-test.md", "ADR-0001", "accepted")
    history_path = tmp_path / "events.jsonl"
    history_path.write_text(
        json.dumps(
            _event(
                "violation_observed",
                "2026-01-01T00:00:00Z",
                adr_id="ADR-0001",
                rule_id="r1",
                fingerprint="f1",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    check_path = tmp_path / "check.jsonl"
    check_path.write_text(
        json.dumps(
            _event(
                "violation_resolved",
                "2026-01-30T00:00:00Z",
                adr_id="ADR-0001",
                rule_id="r1",
                fingerprint="f1",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    adoption_metrics.main(
        [
            "--root",
            str(tmp_path),
            "--dir",
            "docs/decisions",
            "--until",
            "2026-01-31",
            "--events",
            "events.jsonl",
            "--check-results",
            "check.jsonl",
            "--json",
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert result["metrics"]["unresolved_violations"]["open_count"] == 1
    assert any(warning["code"] == "BAD_CHECK_SNAPSHOT" for warning in result["warnings"])


def test_cli_check_record_after_until_does_not_replace_history(tmp_path, capsys):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _write_adr(adr_dir / "0001-test.md", "ADR-0001", "accepted")
    history_path = tmp_path / "events.jsonl"
    history_path.write_text(
        json.dumps(
            _event(
                "violation_observed",
                "2026-01-01T00:00:00Z",
                adr_id="ADR-0001",
                rule_id="r1",
                fingerprint="old",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    check_path = tmp_path / "check.jsonl"
    check_path.write_text(
        json.dumps(
            _event(
                "violation_observed",
                "2026-02-01T00:00:00Z",
                adr_id="ADR-0001",
                rule_id="r2",
                fingerprint="future",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    adoption_metrics.main(
        [
            "--root",
            str(tmp_path),
            "--dir",
            "docs/decisions",
            "--until",
            "2026-01-31",
            "--events",
            "events.jsonl",
            "--check-results",
            "check.jsonl",
            "--json",
        ]
    )

    result = json.loads(capsys.readouterr().out)
    violations = result["metrics"]["unresolved_violations"]
    assert violations["open_count"] == 1
    assert violations["median_age_days"] == 30
    assert any(warning["code"] == "BAD_CHECK_SNAPSHOT" for warning in result["warnings"])


def test_cli_opt_in_github_failure_is_a_warning(tmp_path, capsys, monkeypatch):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    _write_adr(adr_dir / "0001-test.md", "ADR-0001", "accepted")
    monkeypatch.setattr(
        adoption_metrics,
        "collect_github_payload",
        lambda root: (
            None,
            [{"code": "GITHUB_UNAVAILABLE", "detail": "No authenticated provider."}],
        ),
    )

    return_code = adoption_metrics.main(
        [
            "--root",
            str(tmp_path),
            "--dir",
            "docs/decisions",
            "--until",
            "2026-01-31",
            "--github",
            "--json",
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert return_code == 0
    assert [warning["code"] for warning in result["warnings"]] == [
        "GIT_UNAVAILABLE",
        "GITHUB_UNAVAILABLE",
    ]


def test_cli_returns_json_error_for_missing_adr_directory(tmp_path, capsys):
    return_code = adoption_metrics.main(
        ["--root", str(tmp_path), "--dir", "docs/missing", "--json"]
    )

    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert return_code == 1
    assert captured.err == ""
    assert result["ok"] is False
    assert result["errors"][0]["code"] == "ADR_DIR_NOT_FOUND"


def test_cli_returns_json_error_when_adr_directory_escapes_root(tmp_path, capsys):
    outside = tmp_path.parent / "outside-decisions"
    outside.mkdir(exist_ok=True)

    return_code = adoption_metrics.main(
        ["--root", str(tmp_path), "--dir", str(outside), "--json"]
    )

    result = json.loads(capsys.readouterr().out)
    assert return_code == 1
    assert result["errors"] == [
        {
            "code": "PATH_ESCAPES_ROOT",
            "path": str(outside.resolve()),
        }
    ]


def test_cli_returns_json_error_for_invalid_period(tmp_path, capsys):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)

    return_code = adoption_metrics.main(
        [
            "--root",
            str(tmp_path),
            "--dir",
            "docs/decisions",
            "--since",
            "2026-02-01",
            "--until",
            "2026-01-01",
            "--json",
        ]
    )

    result = json.loads(capsys.readouterr().out)
    assert return_code == 1
    assert result["errors"] == [
        {
            "code": "INVALID_PERIOD",
            "detail": "--since must be earlier than or equal to --until.",
        }
    ]
