"""Resolve repository-owned paths independently of the caller's CWD."""
from pathlib import Path


def resolve_from_root(root, path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path(root) / candidate
