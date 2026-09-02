"""Tests for structured stderr logging (docs/adr-toolkit-audit-report.md,
Top-3 #3)."""
import json

from scripts.core import telemetry


def test_get_logger_writes_json_lines_to_stderr(capsys):
    logger = telemetry.get_logger("check", correlation_id="abc123")
    logger.warning("something looked odd")

    captured = capsys.readouterr()
    assert captured.out == ""
    payload = json.loads(captured.err.strip())
    assert payload["level"] == "warning"
    assert payload["operation"] == "check"
    assert payload["correlation_id"] == "abc123"
    assert payload["message"] == "something looked odd"


def test_get_logger_generates_a_correlation_id_when_none_given():
    logger = telemetry.get_logger("index")
    assert logger.extra["correlation_id"]
    assert logger.extra["operation"] == "index"


def test_get_logger_records_exception_type_on_exception_logging(capsys):
    logger = telemetry.get_logger("create")
    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("operation failed")

    captured = capsys.readouterr()
    payload = json.loads(captured.err.strip())
    assert payload["level"] == "error"
    assert payload["exception_type"] == "ValueError"
