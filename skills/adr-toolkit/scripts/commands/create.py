"""Assign the next ADR ID and write a new ADR file from an approved draft."""
import json
from datetime import date
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.schema import validate_frontmatter

REQUIRED_DRAFT_FIELDS = {"title", "status", "body"}


def _prompt(input_fn, question: str) -> str:
    return input_fn(f"{question}\n> ").strip()


def gather_draft_interactively(input_fn=None) -> dict:
    if input_fn is None:
        input_fn = input
    title = _prompt(input_fn, "Title of the decision?")
    problem = _prompt(input_fn, "What problem or constraint made this decision necessary?")
    options_raw = _prompt(input_fn, "Options considered (comma-separated)?")
    options = [o.strip() for o in options_raw.split(",") if o.strip()]
    decision = _prompt(input_fn, "Which option was chosen?")
    rationale = _prompt(input_fn, "Why was it chosen?")
    good = _prompt(input_fn, "One good consequence?")
    bad = _prompt(input_fn, "One accepted downside?")
    confirmation = _prompt(input_fn, "How will this be verified in the code?")
    revisit = _prompt(input_fn, "What condition should reopen this decision?")

    options_block = "\n".join(f"* {o}" for o in options) if options else f"* {decision}"

    body = (
        f"# {title}\n\n"
        "## Context and Problem Statement\n\n"
        f"{problem}\n\n"
        "## Considered Options\n\n"
        f"{options_block}\n\n"
        "## Decision Outcome\n\n"
        f"Chosen option: **{decision}**, because {rationale}.\n\n"
        "## Consequences\n\n"
        f"* Good: {good}\n"
        f"* Bad: {bad}\n\n"
        "## Confirmation\n\n"
        f"{confirmation}\n\n"
        "## Revisit Triggers\n\n"
        f"* {revisit}\n"
    )

    return {"title": title, "status": "proposed", "body": body}


def run(args) -> dict:
    dry_run = getattr(args, "dry_run", False)

    if getattr(args, "interactive", False):
        draft = gather_draft_interactively()
    else:
        input_path = getattr(args, "input", None)
        if not input_path:
            return {
                "ok": False,
                "operation": "create",
                "errors": [{"code": "MISSING_INPUT_OR_INTERACTIVE"}],
            }
        draft = json.loads(Path(input_path).read_text(encoding="utf-8"))

    adr_dir = Path(args.dir)
    missing = REQUIRED_DRAFT_FIELDS - draft.keys()
    if missing:
        return {
            "ok": False,
            "operation": "create",
            "errors": [{"code": "MISSING_DRAFT_FIELD", "fields": sorted(missing)}],
        }

    next_num = identifiers.next_id(adr_dir)
    slug = identifiers.slugify(draft["title"])
    filename = identifiers.format_filename(next_num, slug)
    target = adr_dir / filename

    if target.exists():
        return {
            "ok": False,
            "operation": "create",
            "errors": [{"code": "FILE_ALREADY_EXISTS", "path": str(target)}],
        }

    frontmatter_data = {
        "id": f"ADR-{next_num:04d}",
        "title": draft["title"],
        "status": draft["status"],
        "date": draft.get("date") or date.today().isoformat(),
        "decision_makers": draft.get("decision_makers", []),
        "related": draft.get("related", []),
        "affected_paths": draft.get("affected_paths", []),
        "tags": draft.get("tags", []),
        "retrospective": draft.get("retrospective", False),
    }

    schema_errors = validate_frontmatter(frontmatter_data)
    if schema_errors:
        return {
            "ok": False,
            "operation": "create",
            "errors": [{"code": "SCHEMA_ERROR", "detail": e} for e in schema_errors],
        }

    content = fm.serialize(frontmatter_data, draft["body"].strip() + "\n")

    if dry_run:
        return {"ok": True, "operation": "create", "dry_run": True, "would_create": str(target), "id": frontmatter_data["id"]}

    adr_dir.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return {
        "ok": True,
        "operation": "create",
        "dry_run": False,
        "created": str(target),
        "id": frontmatter_data["id"],
    }
