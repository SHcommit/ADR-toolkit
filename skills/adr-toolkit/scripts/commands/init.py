"""Scaffold a localized ADR directory for a repository that has none yet."""
import json
from datetime import date
from pathlib import Path

from scripts.core.config import (
    CONFIG_FILENAME,
    CONFIG_SCHEMA_VERSION,
    ConfigError,
    resolve_locale,
)
from scripts.core.rendering import render_initial_adr, render_template
from scripts.core.repository_paths import resolve_from_root


def run(args) -> dict:
    root = Path(getattr(args, "root", "."))
    adr_dir = resolve_from_root(root, args.dir)
    dry_run = getattr(args, "dry_run", False)

    if adr_dir.exists() and any(adr_dir.iterdir()):
        return {
            "ok": False,
            "operation": "init",
            "errors": [{"code": "ADR_DIRECTORY_NOT_EMPTY", "path": str(adr_dir)}],
        }

    config_path = root / CONFIG_FILENAME
    config_exists = config_path.is_file()
    try:
        locale = resolve_locale(
            cli_locale=getattr(args, "locale", None),
            draft_locale=None,
            root=root,
        )
    except ConfigError as exc:
        return {
            "ok": False,
            "operation": "init",
            "errors": [{"code": "CONFIG_ERROR", "detail": str(exc)}],
        }

    would_create = [
        str(adr_dir),
        str(adr_dir / "adr-template.md"),
        str(adr_dir / "0001-record-architecture-decisions.md"),
    ]
    if not config_exists:
        would_create.insert(0, str(config_path))

    if dry_run:
        return {"ok": True, "operation": "init", "dry_run": True, "would_create": would_create}

    adr_dir_str = str(args.dir).rstrip("/") + "/"
    title, body = render_initial_adr(locale, adr_dir_str)

    adr_dir.mkdir(parents=True, exist_ok=True)
    (adr_dir / "adr-template.md").write_text(
        render_template(locale, full=False), encoding="utf-8"
    )
    if not config_exists:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps(
                {"schema_version": CONFIG_SCHEMA_VERSION, "locale": locale},
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

    frontmatter_block = (
        "---\n"
        "id: ADR-0001\n"
        f"title: {title}\n"
        "status: accepted\n"
        f"date: {date.today().isoformat()}\n"
        f"locale: {locale}\n"
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
        frontmatter_block + body, encoding="utf-8"
    )

    return {"ok": True, "operation": "init", "dry_run": False, "created": would_create}
