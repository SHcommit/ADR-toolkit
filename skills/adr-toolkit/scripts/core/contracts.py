"""Structural type contracts for ADR Toolkit's JSON command results.

Every command returns a plain dict matching one of these shapes -- typing
them here lets `mypy --strict` (see the `type-check` CI job) catch a test
or caller that reads a field that was renamed or removed. Command
*arguments* are argparse.Namespace objects (dynamic attribute access),
which TypedDict can't model without a larger refactor; that is tracked
separately and not attempted here.
"""
from typing import List, TypedDict


class CommandError(TypedDict, total=False):
    code: str
    detail: str
    correlation_id: str


class BaseResult(TypedDict):
    ok: bool
    operation: str


class ErrorResult(BaseResult):
    errors: List[CommandError]


class CreateResult(BaseResult, total=False):
    dry_run: bool
    created: str
    would_create: str
    id: str
    errors: List[CommandError]
