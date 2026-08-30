import json

import pytest

from scripts import adr


def test_supersede_command_is_registered_with_required_arguments():
    args = adr.build_parser().parse_args(
        ["supersede", "1", "--by", "2", "--dir", "custom/decisions", "--dry-run"]
    )

    assert args.operation == "supersede"
    assert args.adr_number == 1
    assert args.by == 2
    assert args.dir == "custom/decisions"
    assert args.dry_run is True
    assert adr.HANDLERS["supersede"].__module__ == "scripts.commands.supersede"


def test_main_safety_net_converts_unexpected_exception_to_json_error(tmp_path, monkeypatch, capsys):
    def _boom(_args):
        raise RuntimeError("simulated unexpected failure")

    monkeypatch.setitem(adr.HANDLERS, "preflight", _boom)

    exit_code = adr.main(["preflight", "--root", str(tmp_path)])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert captured.out.strip(), "stdout must not be empty"
    payload = json.loads(captured.out)
    assert payload["ok"] is False
    assert payload["operation"] == "preflight"
    assert payload["errors"][0]["code"] == "INTERNAL_ERROR"
    assert "simulated unexpected failure" in payload["errors"][0]["detail"]


def test_index_locale_accepts_every_shipped_locale():
    for code in ("en", "fr", "ja", "ko", "zh"):
        args = adr.build_parser().parse_args(["index", "--locale", code])
        assert args.locale == code


def test_index_locale_rejects_an_unrecognized_code_instead_of_silently_using_english():
    with pytest.raises(SystemExit):
        adr.build_parser().parse_args(["index", "--locale", "zz"])


def test_index_locale_defaults_to_english_when_omitted():
    assert adr.build_parser().parse_args(["index"]).locale == "en"


def test_init_locale_is_optional_and_constrained():
    parser = adr.build_parser()

    assert parser.parse_args(["init"]).locale is None
    assert parser.parse_args(["init", "--locale", "pt-BR"]).locale == "pt-BR"

    with pytest.raises(SystemExit):
        parser.parse_args(["init", "--locale", "xx"])
