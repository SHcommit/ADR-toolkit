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
    exception,
    index,
    init,
    preflight,
    related,
    search,
    significance,
    status,
    supersede,
    validate,
)
from scripts.core.lifecycle import STATUSES
from scripts.core.locale import SUPPORTED_LOCALES


def _add_json_flag(parser: argparse.ArgumentParser) -> None:
    # Every command always prints JSON to stdout (see main()) — there is no
    # human-readable mode. This flag exists only for documentation clarity
    # and backward compatibility with commands that already pass it;
    # omitting it changes nothing.
    parser.add_argument(
        "--json",
        action="store_true",
        help="No effect: output is always JSON. Kept for backward compatibility.",
    )


def _add_diff_mode_arguments(parser: argparse.ArgumentParser) -> None:
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--staged", action="store_true")
    modes.add_argument("--uncommitted", action="store_true")
    modes.add_argument("--since")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="adr.py")
    sub = parser.add_subparsers(dest="operation", required=True)

    p_preflight = sub.add_parser("preflight")
    _add_json_flag(p_preflight)
    p_preflight.add_argument("--root", default=".")

    p_discover = sub.add_parser("discover")
    _add_json_flag(p_discover)
    p_discover.add_argument("--root", default=".")

    p_init = sub.add_parser("init")
    p_init.add_argument("--dir", default="docs/decisions")
    p_init.add_argument("--root", default=".")
    p_init.add_argument("--locale", choices=SUPPORTED_LOCALES)
    p_init.add_argument("--dry-run", dest="dry_run", action="store_true")
    _add_json_flag(p_init)

    p_create = sub.add_parser("create")
    p_create.add_argument("--input")
    p_create.add_argument("--interactive", action="store_true")
    p_create.add_argument("--dir", default="docs/decisions")
    p_create.add_argument("--root", default=".")
    p_create.add_argument("--locale", choices=SUPPORTED_LOCALES)
    p_create.add_argument("--slug")
    p_create.add_argument("--dry-run", dest="dry_run", action="store_true")
    _add_json_flag(p_create)

    p_index = sub.add_parser("index")
    p_index.add_argument("--dir", default="docs/decisions")
    p_index.add_argument("--root", default=".")
    # Constrained so a typo from the agent's own language detection fails
    # visibly instead of silently producing English output.
    p_index.add_argument("--locale", choices=SUPPORTED_LOCALES)
    _add_json_flag(p_index)

    p_related = sub.add_parser("related")
    p_related.add_argument("--paths", nargs="*")
    p_related.add_argument("--tags", nargs="*")
    p_related.add_argument("--keyword")
    p_related.add_argument("--dir", default="docs/decisions")
    _add_json_flag(p_related)

    p_significance = sub.add_parser("significance")
    p_significance.add_argument("--input", required=True)
    _add_json_flag(p_significance)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--dir", default="docs/decisions")
    p_validate.add_argument("--root", default=".")
    _add_json_flag(p_validate)

    p_status = sub.add_parser("status")
    p_status.add_argument("adr_number", type=int)
    p_status.add_argument("--to", required=True)
    p_status.add_argument("--dir", default="docs/decisions")
    p_status.add_argument("--dry-run", dest="dry_run", action="store_true")
    _add_json_flag(p_status)

    p_deprecate = sub.add_parser("deprecate")
    p_deprecate.add_argument("adr_number", type=int)
    p_deprecate.add_argument("--dir", default="docs/decisions")
    p_deprecate.add_argument("--dry-run", dest="dry_run", action="store_true")
    _add_json_flag(p_deprecate)
    p_deprecate.set_defaults(to="deprecated")

    p_supersede = sub.add_parser("supersede")
    p_supersede.add_argument("adr_number", type=int)
    p_supersede.add_argument("--by", type=int, required=True)
    p_supersede.add_argument("--dir", default="docs/decisions")
    p_supersede.add_argument("--dry-run", dest="dry_run", action="store_true")
    _add_json_flag(p_supersede)

    p_diff = sub.add_parser("diff")
    _add_diff_mode_arguments(p_diff)
    p_diff.add_argument("--root", default=".")
    _add_json_flag(p_diff)

    p_check = sub.add_parser("check")
    _add_diff_mode_arguments(p_check)
    p_check.add_argument("--root", default=".")
    p_check.add_argument("--dir", default="docs/decisions")
    _add_json_flag(p_check)

    p_exception = sub.add_parser("exception")
    p_exception.add_argument("--input", required=True)
    p_exception.add_argument("--dir", default="docs/decisions")
    p_exception.add_argument("--root", default=".")
    p_exception.add_argument("--dry-run", dest="dry_run", action="store_true")
    _add_json_flag(p_exception)

    p_search = sub.add_parser("search")
    p_search.add_argument("--keyword")
    p_search.add_argument("--tags", nargs="*")
    p_search.add_argument("--status", choices=sorted(STATUSES))
    p_search.add_argument("--path")
    p_search.add_argument("--limit", type=int)
    p_search.add_argument("--dir", default="docs/decisions")
    _add_json_flag(p_search)

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
    "exception": exception.run,
    "search": search.run,
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
