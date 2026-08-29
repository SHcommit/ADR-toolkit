import json

from scripts import adr


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
