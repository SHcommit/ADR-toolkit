#!/usr/bin/env python3
"""Single entrypoint for all ADR Toolkit deterministic operations."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.commands import (
    check,
    create,
    diff,
    discover,
    index,
    init,
    preflight,
    related,
    significance,
    status,
    supersede,
    validate,
)
from scripts.core.locale import SUPPORTED_LOCALES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="adr.py")
    sub = parser.add_subparsers(dest="operation", required=True)

    p_preflight = sub.add_parser("preflight")
    p_preflight.add_argument("--json", action="store_true")
    p_preflight.add_argument("--root", default=".")

    p_discover = sub.add_parser("discover")
    p_discover.add_argument("--json", action="store_true")
    p_discover.add_argument("--root", default=".")

    p_init = sub.add_parser("init")
    p_init.add_argument("--dir", default="docs/decisions")
    p_init.add_argument("--root", default=".")
    p_init.add_argument("--locale", choices=SUPPORTED_LOCALES)
    p_init.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_init.add_argument("--json", action="store_true")

    p_create = sub.add_parser("create")
    p_create.add_argument("--input")
    p_create.add_argument("--interactive", action="store_true")
    p_create.add_argument("--dir", default="docs/decisions")
    p_create.add_argument("--root", default=".")
    p_create.add_argument("--locale", choices=SUPPORTED_LOCALES)
    p_create.add_argument("--slug")
    p_create.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_create.add_argument("--json", action="store_true")

    p_index = sub.add_parser("index")
    p_index.add_argument("--dir", default="docs/decisions")
    # Constrained so a typo from the agent's own language detection fails
    # visibly instead of silently producing English output.
    p_index.add_argument("--locale", default="en", choices=["en", "fr", "ja", "ko", "zh"])
    p_index.add_argument("--json", action="store_true")

    p_related = sub.add_parser("related")
    p_related.add_argument("--paths", nargs="*")
    p_related.add_argument("--tags", nargs="*")
    p_related.add_argument("--keyword")
    p_related.add_argument("--dir", default="docs/decisions")
    p_related.add_argument("--json", action="store_true")

    p_significance = sub.add_parser("significance")
    p_significance.add_argument("--input", required=True)
    p_significance.add_argument("--json", action="store_true")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--dir", default="docs/decisions")
    p_validate.add_argument("--json", action="store_true")

    p_status = sub.add_parser("status")
    p_status.add_argument("adr_number", type=int)
    p_status.add_argument("--to", required=True)
    p_status.add_argument("--dir", default="docs/decisions")
    p_status.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_status.add_argument("--json", action="store_true")

    p_deprecate = sub.add_parser("deprecate")
    p_deprecate.add_argument("adr_number", type=int)
    p_deprecate.add_argument("--dir", default="docs/decisions")
    p_deprecate.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_deprecate.add_argument("--json", action="store_true")
    p_deprecate.set_defaults(to="deprecated")

    p_supersede = sub.add_parser("supersede")
    p_supersede.add_argument("adr_number", type=int)
    p_supersede.add_argument("--by", type=int, required=True)
    p_supersede.add_argument("--dir", default="docs/decisions")
    p_supersede.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_supersede.add_argument("--json", action="store_true")

    p_diff = sub.add_parser("diff")
    p_diff.add_argument("--staged", action="store_true")
    p_diff.add_argument("--uncommitted", action="store_true")
    p_diff.add_argument("--since")
    p_diff.add_argument("--root", default=".")
    p_diff.add_argument("--json", action="store_true")

    p_check = sub.add_parser("check")
    p_check.add_argument("--staged", action="store_true")
    p_check.add_argument("--uncommitted", action="store_true")
    p_check.add_argument("--since")
    p_check.add_argument("--root", default=".")
    p_check.add_argument("--dir", default="docs/decisions")
    p_check.add_argument("--json", action="store_true")

    return parser


HANDLERS = {
    "preflight": preflight.run,
    "discover": discover.run,
    "init": init.run,
    "create": create.run,
    "index": index.run,
    "related": related.run,
    "significance": significance.run,
    "validate": validate.run,
    "status": status.run,
    "deprecate": status.run,
    "supersede": supersede.run,
    "diff": diff.run,
    "check": check.run,
}


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = HANDLERS[args.operation](args)
    except Exception as exc:  # noqa: BLE001 - last-resort safety net for the JSON-only-stdout contract
        result = {
            "ok": False,
            "operation": args.operation,
            "errors": [{"code": "INTERNAL_ERROR", "detail": str(exc)}],
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
