"""Load deterministic strings for ADR scaffolds, prompts, and indexes."""
import json
from pathlib import Path

I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"
SUPPORTED_LOCALES = ("en", "ko", "ja", "zh", "fr", "es", "de", "pt-BR")
DEFAULT_LOCALE = "en"


def load_locale(locale: str) -> dict:
    base = _load_json(DEFAULT_LOCALE)
    if locale == DEFAULT_LOCALE:
        return base
    overlay = _load_json(locale)
    return {**base, **overlay}


def _load_json(locale: str) -> dict:
    path = I18N_DIR / f"{locale}.json"
    if not path.is_file():
        return {}
    # A malformed or unreadable locale file degrades to "no overlay", exactly
    # like a missing one. Localization is cosmetic; per design spec §17.1 it
    # must never turn into a crash for an otherwise valid index run.
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
