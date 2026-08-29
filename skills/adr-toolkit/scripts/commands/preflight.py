"""Check that the environment has what ADR Toolkit needs to run."""
import shutil
import sys
from pathlib import Path

CANDIDATE_ADR_DIRS = ("docs/decisions", "docs/adr", "adr", "decisions")


def run(args) -> dict:
    errors = []

    if sys.version_info < (3, 9):
        errors.append({"code": "PYTHON_TOO_OLD", "detail": sys.version})

    git_path = shutil.which("git")

    root = Path(getattr(args, "root", ".")).resolve()
    existing_dir = None
    for candidate in CANDIDATE_ADR_DIRS:
        if (root / candidate).is_dir():
            existing_dir = candidate
            break

    warnings = []
    if git_path is None:
        warnings.append({"code": "GIT_NOT_FOUND"})

    return {
        "ok": not errors,
        "operation": "preflight",
        "python_version": sys.version.split()[0],
        "git_available": git_path is not None,
        "existing_adr_directory": existing_dir,
        "warnings": warnings,
        "errors": errors,
    }
