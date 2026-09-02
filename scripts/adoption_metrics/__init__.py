"""ADR adoption metrics package."""

from .collection import (
    collect_git_events,
    collect_github_payload,
    merge_events,
    normalize_github_reviews,
    read_adrs,
    read_check_snapshot,
    read_events,
    read_exceptions,
)
from .common import parse_timestamp
from .calculation import calculate_metrics
from .reporting import (
    CollectionError,
    JsonArgumentParser,
    build_report,
    github_adr_paths,
    main,
)

__all__ = [
    "CollectionError",
    "JsonArgumentParser",
    "build_report",
    "calculate_metrics",
    "collect_git_events",
    "collect_github_payload",
    "github_adr_paths",
    "main",
    "merge_events",
    "normalize_github_reviews",
    "parse_timestamp",
    "read_adrs",
    "read_check_snapshot",
    "read_events",
    "read_exceptions",
]
