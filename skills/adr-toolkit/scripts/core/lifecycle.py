"""ADR status lifecycle rules."""

STATUSES = {"proposed", "accepted", "rejected", "deprecated", "superseded"}

ALLOWED_TRANSITIONS = {
    "proposed": {"accepted", "rejected"},
    "accepted": {"deprecated", "superseded"},
    "rejected": set(),
    "deprecated": set(),
    "superseded": set(),
}


class InvalidTransitionError(ValueError):
    pass


def validate_transition(current: str, target: str) -> None:
    if current not in STATUSES:
        raise InvalidTransitionError(f"Unknown current status: {current!r}")
    if target not in STATUSES:
        raise InvalidTransitionError(f"Unknown target status: {target!r}")
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransitionError(f"Cannot transition from {current!r} to {target!r}")
