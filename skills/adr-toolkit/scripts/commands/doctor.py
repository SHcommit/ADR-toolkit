"""Diagnose local ADR Toolkit repository health and suggest safe repairs."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core.adr_directory import iter_adr_files
from scripts.core.config import CONFIG_FILENAME, ConfigError, load_repository_config
from scripts.core.repository_paths import resolve_from_root_or_error


CONFIG_REPAIR = (
    "Edit .adr-toolkit.json so schema_version is 1, locale is supported, "
    "and adr_dir is a relative path inside the repository."
)
FRONTMATTER_REPAIR = (
    "Restore a valid YAML frontmatter block delimited by --- with required ADR fields."
)
LOCK_REPAIR = "If no adr command is running, remove .adr/lock and rerun the command."


def run(args) -> dict:
    root = Path(getattr(args, "root", ".")).resolve()
    diagnostics = []
    checked = {
        "config": True,
        "frontmatter_files": 0,
        "lock": True,
    }

    try:
        load_repository_config(root)
    except ConfigError as exc:
        diagnostics.append(
            {
                "code": "CONFIG_ERROR",
                "file": CONFIG_FILENAME,
                "detail": str(exc),
                "repair": CONFIG_REPAIR,
            }
        )

    adr_dir, error = resolve_from_root_or_error(root, args.dir, operation="doctor")
    if error:
        diagnostics.extend(error.get("errors", []))
    elif adr_dir.is_dir():
        for path, _ in iter_adr_files(adr_dir):
            checked["frontmatter_files"] += 1
            try:
                fm.parse(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, fm.FrontmatterError) as exc:
                diagnostics.append(
                    {
                        "code": "BAD_FRONTMATTER",
                        "file": path.name,
                        "detail": str(exc),
                        "repair": FRONTMATTER_REPAIR,
                    }
                )

    lock_path = root / ".adr" / "lock"
    if lock_path.exists():
        diagnostics.append(
            {
                "code": "STALE_LOCK",
                "path": str(lock_path),
                "detail": "ADR Toolkit lock file exists.",
                "repair": LOCK_REPAIR,
            }
        )

    return {
        "ok": not diagnostics,
        "operation": "doctor",
        "checked": checked,
        "diagnostics": diagnostics,
    }
