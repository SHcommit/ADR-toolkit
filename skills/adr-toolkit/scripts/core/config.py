"""Load and validate repository-owned ADR Toolkit configuration."""
import json
from pathlib import Path
from typing import Optional

from scripts.core.locale import DEFAULT_LOCALE, SUPPORTED_LOCALES

CONFIG_FILENAME = ".adr-toolkit.json"
CONFIG_SCHEMA_VERSION = 1
ALLOWED_KEYS = {"schema_version", "locale"}


class ConfigError(ValueError):
    """The repository configuration is malformed or unsupported."""


def load_repository_config(root: Path) -> dict:
    path = Path(root) / CONFIG_FILENAME
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Invalid {CONFIG_FILENAME}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{CONFIG_FILENAME} must contain a JSON object")
    unknown = set(data) - ALLOWED_KEYS
    if unknown:
        raise ConfigError(f"Unknown config fields: {sorted(unknown)}")
    if data.get("schema_version") != CONFIG_SCHEMA_VERSION:
        raise ConfigError(
            f"Unsupported schema_version: {data.get('schema_version')!r}"
        )
    if data.get("locale") not in SUPPORTED_LOCALES:
        raise ConfigError(f"Unsupported locale: {data.get('locale')!r}")
    return data


def resolve_locale(
    *,
    cli_locale: Optional[str],
    draft_locale: Optional[str],
    root: Path,
) -> str:
    config = load_repository_config(Path(root))
    locale = cli_locale or draft_locale or config.get("locale") or DEFAULT_LOCALE
    if locale not in SUPPORTED_LOCALES:
        raise ConfigError(f"Unsupported locale: {locale!r}")
    return locale
