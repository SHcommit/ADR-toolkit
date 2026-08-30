"""Scan the repository for evidence of existing conventions and past decisions."""
from pathlib import Path

from scripts.evidence import dependency_scanner


def run(args) -> dict:
    root = Path(getattr(args, "root", ".")).resolve()
    dependencies = dependency_scanner.scan(root)

    return {
        "ok": True,
        "operation": "discover",
        "root": str(root),
        "dependencies": dependencies,
        "warnings": [],
    }
