"""Structural type contracts for ADR Toolkit's JSON command results.

Every command returns a plain dict matching one of these shapes -- typing
them here lets `mypy --strict` (see the `type-check` CI job) catch a test
or caller that reads a field that was renamed or removed. Command
*arguments* are argparse.Namespace objects (dynamic attribute access),
which TypedDict can't model without a larger refactor; that is tracked
separately and not attempted here.
"""
from typing import Any, Dict, List, Optional, TypedDict


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
    warnings: List[Dict[str, Any]]
    errors: List[CommandError]


class CheckFinding(TypedDict, total=False):
    adr_id: str
    kind: str
    confidence: str
    rule_id: str
    severity: str
    message: str
    file: str
    evidence: Dict[str, Any]
    resolutions: List[str]
    exception: Dict[str, Any]


class CheckResult(BaseResult, total=False):
    diff: Dict[str, Any]
    findings: List[CheckFinding]
    warnings: List[Dict[str, Any]]
    errors: List[CommandError]


class PreflightResult(BaseResult):
    python_version: str
    git_available: bool
    existing_adr_directory: Optional[str]
    warnings: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class DiscoverResult(BaseResult):
    root: str
    dependencies: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]


class InitResult(BaseResult, total=False):
    dry_run: bool
    created: List[str]
    would_create: List[str]
    errors: List[Dict[str, Any]]


class IndexResult(BaseResult, total=False):
    count: int
    path: str
    warnings: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class RelatedResult(BaseResult):
    count: int
    matches: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]


class SignificanceResult(BaseResult, total=False):
    total: int
    classification: str
    errors: List[Dict[str, Any]]


class ValidateResult(BaseResult):
    checked: int
    errors: List[Dict[str, Any]]


class StatusResult(BaseResult, total=False):
    dry_run: bool
    would_update: str
    updated: str
    to: str
    warnings: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class SupersedeResult(BaseResult, total=False):
    dry_run: bool
    would_update: List[str]
    old: str
    new: str
    errors: List[Dict[str, Any]]


class DiffResult(BaseResult, total=False):
    mode: str
    ref: Optional[str]
    files: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class ExceptionResult(BaseResult, total=False):
    dry_run: bool
    created: str
    would_create: str
    id: str
    errors: List[Dict[str, Any]]


class GraphResult(BaseResult, total=False):
    count: int
    outputs: List[str]
    warnings: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class SearchResult(BaseResult):
    query: Dict[str, Any]
    count: int
    total: int
    truncated: bool
    results: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
