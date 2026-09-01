"""Resolve repository-owned paths independently of the caller's CWD."""
from pathlib import Path


class PathEscapesRootError(ValueError):
    """A relative path resolved outside the root it was given against."""


def resolve_from_root(root, path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        # An explicit absolute path is the caller's own responsibility --
        # there's no relative containment to check. Only a *relative*
        # `path` can accidentally (or maliciously) walk out of `root`.
        return candidate

    joined = Path(root) / candidate
    root_resolved = Path(root).resolve()
    if not joined.resolve().is_relative_to(root_resolved):
        raise PathEscapesRootError(f"{str(path)!r} escapes root {str(root)!r}")
    return joined
