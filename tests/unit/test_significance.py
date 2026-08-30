import pytest

from scripts.rules import significance


FULL_SCORES = {c: 2 for c in significance.CRITERIA}
ZERO_SCORES = {c: 0 for c in significance.CRITERIA}


def test_score_sums_all_seven_criteria():
    assert significance.score(FULL_SCORES) == 14
    assert significance.score(ZERO_SCORES) == 0


def test_score_defaults_missing_criteria_to_zero():
    assert significance.score({}) == 0


def test_score_rejects_out_of_range_value():
    with pytest.raises(ValueError):
        significance.score({"reversal_cost": 3})


def test_classify_bands():
    assert significance.classify(0) == "not_needed"
    assert significance.classify(3) == "not_needed"
    assert significance.classify(4) == "optional"
    assert significance.classify(6) == "optional"
    assert significance.classify(7) == "recommended"
    assert significance.classify(14) == "recommended"
