"""Verifies adr.py's global exception handler surfaces a correlation ID in
both the stdout JSON error and the stderr structured log (Top-3 #3)."""
import json

from scripts import adr


def test_internal_error_includes_correlation_id_and_stderr_log(monkeypatch, capsys):
    def _boom(args):
        raise RuntimeError("boom")

    monkeypatch.setitem(adr.HANDLERS, "preflight", _boom)

    exit_code = adr.main(["preflight"])

    assert exit_code == 1
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["ok"] is False
    assert result["errors"][0]["code"] == "INTERNAL_ERROR"
    correlation_id = result["errors"][0]["correlation_id"]
    assert correlation_id

    log_payload = json.loads(captured.err.strip().splitlines()[-1])
    assert log_payload["level"] == "error"
    assert log_payload["operation"] == "preflight"
    assert log_payload["correlation_id"] == correlation_id
