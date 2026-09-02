"""Common base for ADR Toolkit's domain-specific exceptions.

Lets a caller catch "any ADR Toolkit domain error" in one except clause,
and gives every such error a stable, class-level error_code instead of
each call site retyping the same string.
"""


class AdrToolkitError(Exception):
    error_code: str = "UNKNOWN_ERROR"
