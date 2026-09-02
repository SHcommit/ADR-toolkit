"""Resolve repository-owned paths independently of the caller's CWD."""
import os
from pathlib import Path

from scripts.core.errors import AdrToolkitError


class PathEscapesRootError(AdrToolkitError):
    """A relative path resolved outside the root it was given against."""
    error_code = "PATH_ESCAPES_ROOT"


def resolve_from_root(root, path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        # An explicit absolute path is the caller's own responsibility --
        # there's no relative containment to check. Only a *relative*
        # `path` can accidentally (or maliciously) walk out of `root`.
        return candidate

    joined = Path(root) / candidate
    root_resolved = Path(root).resolve()
    # `joined` (e.g. INIT scaffolding a brand new "docs/decisions") commonly
    # doesn't exist on disk yet. Path.resolve() on a non-existent path has
    # inconsistent cross-version behavior on Windows (observed: Python 3.9
    # rejects a legitimate under-root path that Python 3.12 accepts
    # identically), so the containment check is done with pure lexical
    # normalization (os.path.normpath, no filesystem access) against the
    # already-resolved root instead of resolving the joined path itself.
    joined_normalized = Path(os.path.normpath(str(root_resolved / candidate)))
    if not joined_normalized.is_relative_to(root_resolved):
        raise PathEscapesRootError(f"{str(path)!r} escapes root {str(root)!r}")
    return joined


def resolve_from_root_or_error(root, path, *, operation: str):
    """Same as resolve_from_root, but converts a rejected escape into the
    same {"ok": False, "operation": ..., "errors": [...]} shape every
    other domain error already gets at its call site, instead of falling
    through to adr.py's generic INTERNAL_ERROR. Returns (Path, None) on
    success or (None, error_dict) on rejection."""
    try:
        return resolve_from_root(root, path), None
    except PathEscapesRootError as exc:
        return None, {
            "ok": False,
            "operation": operation,
            "errors": [{"code": exc.error_code, "detail": str(exc)}],
        }
