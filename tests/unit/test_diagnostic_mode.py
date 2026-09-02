"""Tests for the --diagnostic timing flag (docs/adr-toolkit-audit-report.md
§2.7 7.2)."""
import json

from scripts import adr


def test_diagnostic_flag_adds_elapsed_ms(tmp_path, capsys):
    exit_code = adr.main(["--diagnostic", "preflight", "--root", str(tmp_path)])

    assert exit_code == 0
    result = json.loads(capsys.readouterr().out)
    assert "_diagnostics" in result
    assert isinstance(result["_diagnostics"]["elapsed_ms"], (int, float))
    assert result["_diagnostics"]["elapsed_ms"] >= 0


def test_diagnostic_flag_omitted_by_default(tmp_path, capsys):
    exit_code = adr.main(["preflight", "--root", str(tmp_path)])

    assert exit_code == 0
    result = json.loads(capsys.readouterr().out)
    assert "_diagnostics" not in result
