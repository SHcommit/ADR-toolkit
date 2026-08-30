"""Load i18n locale files for index.py's generated strings.

Every other user-facing string in this toolkit (RECORD/DISCOVER/CHECK's
interview questions and reports) is composed by the agent, not a fixed
Python string, so it needs no translation table — only index.py's
generated README.md content is a translation target (design spec §17.1).
"""
import json
from pathlib import Path

I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"
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
    return json.loads(path.read_text(encoding="utf-8"))
