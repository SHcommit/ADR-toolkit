#!/usr/bin/env python3
"""Export the pinned ``dev`` extra from pyproject.toml as requirements."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]


def dev_requirements(pyproject: Path) -> list[str]:
    with pyproject.open("rb") as stream:
        document = tomllib.load(stream)
    return list(document["project"]["optional-dependencies"]["dev"])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pyproject", type=Path, default=Path("pyproject.toml"))
    args = parser.parse_args(argv)
    print(*dev_requirements(args.pyproject), sep="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
