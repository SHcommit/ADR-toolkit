"""Load and validate repository-owned ADR Toolkit configuration."""
import json
import os
from pathlib import Path
from typing import Optional

from scripts.core.errors import AdrToolkitError
from scripts.core.locale import DEFAULT_LOCALE, SUPPORTED_LOCALES

CONFIG_FILENAME = ".adr-toolkit.json"
CONFIG_SCHEMA_VERSION = 1
ALLOWED_KEYS = {"schema_version", "locale", "adr_dir"}
DEFAULT_ADR_DIR = "docs/decisions"


class ConfigError(AdrToolkitError):
    """The repository configuration is malformed or unsupported."""
    error_code = "CONFIG_ERROR"


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
    if "locale" in data and data["locale"] not in SUPPORTED_LOCALES:
        raise ConfigError(f"Unsupported locale: {data.get('locale')!r}")
    if "adr_dir" in data:
        adr_dir = data["adr_dir"]
        if not isinstance(adr_dir, str) or not adr_dir.strip():
            raise ConfigError("adr_dir must be a non-empty string")
        if adr_dir.startswith("/") or ".." in Path(adr_dir).parts:
            raise ConfigError("adr_dir must be a valid relative path without path escape")
    return data


def resolve_adr_dir(*, cli_dir: Optional[str], root: Path) -> Path:
    """Resolve the active ADR directory path.

    Precedence:
    1. Explicit cli_dir (if provided and differs from default or explicitly requested)
    2. ADR_DIR environment variable
    3. adr_dir in .adr-toolkit.json
    4. Default 'docs/decisions'
    """
    env_dir = os.getenv("ADR_DIR", "").strip()
    config = load_repository_config(Path(root))
    config_dir = config.get("adr_dir")

    if cli_dir and cli_dir != DEFAULT_ADR_DIR:
        selected = cli_dir
    elif env_dir:
        selected = env_dir
    elif config_dir:
        selected = config_dir
    elif cli_dir:
        selected = cli_dir
    else:
        selected = DEFAULT_ADR_DIR

    return Path(root) / selected


def resolve_locale(
    *,
    cli_locale: Optional[str],
    draft_locale: Optional[str],
    root: Path,
) -> str:
    """Resolve the active locale string.

    Precedence:
    1. Explicit cli_locale
    2. Draft metadata draft_locale
    3. ADR_LOCALE environment variable
    4. locale in .adr-toolkit.json
    5. Default locale ('en')
    """
    env_locale = os.getenv("ADR_LOCALE", "").strip()
    config = load_repository_config(Path(root))
    locale = cli_locale or draft_locale or env_locale or config.get("locale") or DEFAULT_LOCALE
    if locale not in SUPPORTED_LOCALES:
        raise ConfigError(f"Unsupported locale: {locale!r}")
    return locale

