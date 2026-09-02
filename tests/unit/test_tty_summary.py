"""Tests for the TTY-only human summary line
(docs/adr-toolkit-audit-report.md §2.6 6.2)."""
import sys

from scripts import adr


def test_summary_line_appears_when_stderr_is_a_tty(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)
    monkeypatch.delenv("ADR_TOOLKIT_NO_COLOR", raising=False)

    exit_code = adr.main(["preflight", "--root", str(tmp_path)])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "preflight" in captured.err
    assert "ok" in captured.err


def test_no_summary_line_when_stderr_is_not_a_tty(tmp_path, capsys):
    # capsys-captured stderr is not a real TTY by default -- this is the
    # common redirected/piped case, e.g. `adr.py check ... | jq`.
    exit_code = adr.main(["preflight", "--root", str(tmp_path)])

    assert exit_code == 0
    assert capsys.readouterr().err == ""


def test_no_summary_line_when_no_color_env_is_set(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)
    monkeypatch.setenv("ADR_TOOLKIT_NO_COLOR", "1")

    adr.main(["preflight", "--root", str(tmp_path)])

    assert capsys.readouterr().err == ""
