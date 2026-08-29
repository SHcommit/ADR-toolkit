#!/usr/bin/env python3
"""Single entrypoint for all ADR Toolkit deterministic operations."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.commands import preflight, discover, init, create, index, validate


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
    p_init.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_init.add_argument("--json", action="store_true")

    p_create = sub.add_parser("create")
    p_create.add_argument("--input")
    p_create.add_argument("--interactive", action="store_true")
    p_create.add_argument("--dir", default="docs/decisions")
    p_create.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_create.add_argument("--json", action="store_true")

    p_index = sub.add_parser("index")
    p_index.add_argument("--dir", default="docs/decisions")
    p_index.add_argument("--json", action="store_true")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--dir", default="docs/decisions")
    p_validate.add_argument("--json", action="store_true")

    return parser


HANDLERS = {
    "preflight": preflight.run,
    "discover": discover.run,
    "init": init.run,
    "create": create.run,
    "index": index.run,
    "validate": validate.run,
}


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = HANDLERS[args.operation](args)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
