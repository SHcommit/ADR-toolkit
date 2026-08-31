"""Shared ADR-candidate file iteration for related/index/validate/check."""
from pathlib import Path

from scripts.core import identifiers

SKIP_FILES = {"README.md", "adr-template.md"}


def iter_adr_files(adr_dir: Path):
    """Yield (path, parsed) for every candidate ADR file in `adr_dir`, sorted.

    Skips known non-ADR files (README.md, adr-template.md). `parsed` is the
    `identifiers.parse_filename()` result — None when the filename doesn't
    match the ADR-NNNN-slug pattern. Callers decide whether that is a silent
    skip or a reportable error.
    """
    for path in sorted(adr_dir.glob("*.md")):
        if path.name in SKIP_FILES:
            continue
        yield path, identifiers.parse_filename(path.name)
