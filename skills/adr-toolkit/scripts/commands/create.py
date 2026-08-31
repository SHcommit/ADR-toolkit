"""Assign the next ADR ID and write a new ADR file from an approved draft."""
import json
import sys
from datetime import date
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.config import ConfigError, resolve_locale
from scripts.core.locale import DEFAULT_LOCALE
from scripts.core.rendering import interactive_prompts, render_minimal
from scripts.core.repository_paths import resolve_from_root
from scripts.core.schema import validate_frontmatter

REQUIRED_DRAFT_FIELDS = {"title", "status", "body"}


def _prompt(input_fn, question: str) -> str:
    print(question, file=sys.stderr)
    print("> ", end="", file=sys.stderr)
    return input_fn("").strip()


def gather_draft_interactively(locale: str = DEFAULT_LOCALE, input_fn=None) -> dict:
    if input_fn is None:
        input_fn = input
    prompts = interactive_prompts(locale)
    title = _prompt(input_fn, prompts[0])
    problem = _prompt(input_fn, prompts[1])
    options_raw = _prompt(input_fn, prompts[2])
    options = [o.strip() for o in options_raw.split(",") if o.strip()]
    decision = _prompt(input_fn, prompts[3])
    rationale = _prompt(input_fn, prompts[4])
    good = _prompt(input_fn, prompts[5])
    bad = _prompt(input_fn, prompts[6])
    confirmation = _prompt(input_fn, prompts[7])
    revisit = _prompt(input_fn, prompts[8])

    body = render_minimal(locale, {
        "title": title,
        "problem": problem,
        "options": options or [decision],
        "decision": decision,
        "rationale": rationale,
        "good": good,
        "bad": bad,
        "confirmation": confirmation,
        "revisit": revisit,
    })

    return {"title": title, "status": "proposed", "body": body, "locale": locale}


def run(args) -> dict:
    dry_run = getattr(args, "dry_run", False)
    root = Path(getattr(args, "root", "."))

    if getattr(args, "interactive", False):
        try:
            locale = resolve_locale(
                cli_locale=getattr(args, "locale", None),
                draft_locale=None,
                root=root,
            )
        except ConfigError as exc:
            return {
                "ok": False,
                "operation": "create",
                "errors": [{"code": "CONFIG_ERROR", "detail": str(exc)}],
            }
        draft = gather_draft_interactively(locale)
    else:
        input_path = getattr(args, "input", None)
        if not input_path:
            return {
                "ok": False,
                "operation": "create",
                "errors": [{"code": "MISSING_INPUT_OR_INTERACTIVE"}],
            }
        try:
            raw_draft = Path(input_path).read_text(encoding="utf-8")
        except FileNotFoundError:
            return {
                "ok": False,
                "operation": "create",
                "errors": [{"code": "DRAFT_FILE_NOT_FOUND", "path": input_path}],
            }
        try:
            draft = json.loads(raw_draft)
        except json.JSONDecodeError as exc:
            return {
                "ok": False,
                "operation": "create",
                "errors": [{"code": "DRAFT_FILE_INVALID_JSON", "path": input_path, "detail": str(exc)}],
            }

        try:
            locale = resolve_locale(
                cli_locale=getattr(args, "locale", None),
                draft_locale=draft.get("locale"),
                root=root,
            )
        except ConfigError as exc:
            return {
                "ok": False,
                "operation": "create",
                "errors": [{"code": "CONFIG_ERROR", "detail": str(exc)}],
            }

    adr_dir = resolve_from_root(root, args.dir)
    missing = REQUIRED_DRAFT_FIELDS - draft.keys()
    if missing:
        return {
            "ok": False,
            "operation": "create",
            "errors": [{"code": "MISSING_DRAFT_FIELD", "fields": sorted(missing)}],
        }

    cli_slug = getattr(args, "slug", None)
    draft_slug = draft.get("slug")
    if cli_slug is not None and draft_slug is not None and cli_slug != draft_slug:
        return {
            "ok": False,
            "operation": "create",
            "errors": [{"code": "CONFLICTING_SLUG_INPUT"}],
        }
    try:
        slug = identifiers.slug_for_title(draft["title"], cli_slug or draft_slug)
    except ValueError as exc:
        return {
            "ok": False,
            "operation": "create",
            "errors": [{"code": "INVALID_SLUG", "detail": str(exc)}],
        }

    next_num = identifiers.next_id(adr_dir)
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
        "locale": locale,
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
