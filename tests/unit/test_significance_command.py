import json
from types import SimpleNamespace

from scripts.commands import significance


def test_significance_command_returns_total_and_classification(tmp_path):
    input_path = tmp_path / "scores.json"
    input_path.write_text(
        json.dumps({"reversal_cost": 2, "boundary_or_pattern_change": 2}),
        encoding="utf-8",
    )

    result = significance.run(SimpleNamespace(input=str(input_path)))

    assert result["ok"] is True
    assert result["total"] == 4
    assert result["classification"] == "optional"


def test_significance_command_rejects_bad_score(tmp_path):
    input_path = tmp_path / "scores.json"
    input_path.write_text(json.dumps({"reversal_cost": 9}), encoding="utf-8")

    result = significance.run(SimpleNamespace(input=str(input_path)))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "INVALID_SCORE"
