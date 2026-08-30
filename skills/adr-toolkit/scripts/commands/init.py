"""Scaffold an ADR directory for a repository that has none yet."""
import shutil
from datetime import date
from pathlib import Path

TEMPLATE_SOURCE = Path(__file__).resolve().parent.parent.parent / "templates" / "madr-minimal.md"

INITIAL_ADR_BODY = """# Record architecture decisions

## Context and Problem Statement

We need a consistent way to capture and communicate significant
architectural decisions so future contributors (human or agent) can find
the reasoning behind them.

## Considered Options

* No formal record, rely on commit messages and memory
* Wiki or external documentation tool
* Architecture Decision Records stored alongside the code

## Decision Outcome

Chosen option: **Architecture Decision Records stored alongside the code**, because they version with the code, stay close to what they describe, and are readable by both humans and coding agents.

## Consequences

* Good: decisions and their rationale are discoverable in the repository itself.
* Bad: requires discipline to keep records up to date as decisions evolve.

## Confirmation

* [ ] `{adr_dir}` exists with this file, a template, and an index.

## Revisit Triggers

* The team adopts a different documentation system project-wide.
"""


def run(args) -> dict:
    adr_dir = Path(args.dir)
    dry_run = getattr(args, "dry_run", False)

    if adr_dir.exists() and any(adr_dir.iterdir()):
        return {
            "ok": False,
            "operation": "init",
            "errors": [{"code": "ADR_DIRECTORY_NOT_EMPTY", "path": str(adr_dir)}],
        }

    would_create = [
        str(adr_dir),
        str(adr_dir / "adr-template.md"),
        str(adr_dir / "0001-record-architecture-decisions.md"),
    ]

    if dry_run:
        return {"ok": True, "operation": "init", "dry_run": True, "would_create": would_create}

    adr_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE_SOURCE, adr_dir / "adr-template.md")

    adr_dir_str = str(args.dir).rstrip("/") + "/"

    frontmatter_block = (
        "---\n"
        "id: ADR-0001\n"
        "title: Record architecture decisions\n"
        "status: accepted\n"
        f"date: {date.today().isoformat()}\n"
        "decision_makers: []\n"
        "related: []\n"
        "affected_paths:\n"
        f"  - {adr_dir_str}\n"
        "tags:\n"
        "  - process\n"
        "retrospective: false\n"
        "---\n\n"
    )
    (adr_dir / "0001-record-architecture-decisions.md").write_text(
        frontmatter_block + INITIAL_ADR_BODY.format(adr_dir=adr_dir_str), encoding="utf-8"
    )

    return {"ok": True, "operation": "init", "dry_run": False, "created": would_create}
