import pytest

from scripts.core import lifecycle


def test_proposed_can_become_accepted():
    lifecycle.validate_transition("proposed", "accepted")  # must not raise


def test_proposed_can_become_rejected():
    lifecycle.validate_transition("proposed", "rejected")  # must not raise


def test_accepted_cannot_go_back_to_proposed():
    with pytest.raises(lifecycle.InvalidTransitionError):
        lifecycle.validate_transition("accepted", "proposed")


def test_rejected_is_terminal():
    with pytest.raises(lifecycle.InvalidTransitionError):
        lifecycle.validate_transition("rejected", "accepted")


def test_unknown_status_is_rejected():
    with pytest.raises(lifecycle.InvalidTransitionError):
        lifecycle.validate_transition("accepted", "archived")
