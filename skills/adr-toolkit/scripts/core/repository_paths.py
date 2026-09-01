"""Resolve repository-owned paths independently of the caller's CWD."""
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
    if not joined.resolve().is_relative_to(root_resolved):
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
