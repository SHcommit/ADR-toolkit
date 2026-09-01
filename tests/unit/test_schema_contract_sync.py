"""Detects drift between the hand-rolled runtime validators and the JSON
Schema files in schemas/ that document the same shape for external tools
(docs/adr-toolkit-audit-report.md §2.4 4.2).

Deliberately stdlib-only -- this project has zero third-party runtime
dependencies by design, and adopting the `jsonschema` library just to keep
two already-hand-maintained definitions in sync would be a worse trade
than a plain field-name/enum comparison."""
import json
from pathlib import Path

from scripts.core.exceptions import REQUIRED_FIELDS as EXCEPTION_REQUIRED_FIELDS
from scripts.core.lifecycle import STATUSES
from scripts.core.locale import SUPPORTED_LOCALES
from scripts.core.schema import REQUIRED_FIELDS as ADR_REQUIRED_FIELDS

_SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "skills" / "adr-toolkit" / "schemas"


def _load_schema(filename: str) -> dict:
    return json.loads((_SCHEMAS_DIR / filename).read_text(encoding="utf-8"))


def test_adr_schema_required_fields_match_the_runtime_validator():
    schema = _load_schema("adr.schema.json")
    assert set(schema["required"]) == set(ADR_REQUIRED_FIELDS)


def test_adr_schema_status_enum_matches_the_runtime_lifecycle_statuses():
    schema = _load_schema("adr.schema.json")
    assert set(schema["properties"]["status"]["enum"]) == STATUSES


def test_adr_schema_locale_enum_matches_the_runtime_supported_locales():
    schema = _load_schema("adr.schema.json")
    assert set(schema["properties"]["locale"]["enum"]) == set(SUPPORTED_LOCALES)


def test_exception_schema_required_fields_match_the_runtime_validator():
    schema = _load_schema("exception.schema.json")
    assert set(schema["required"]) == set(EXCEPTION_REQUIRED_FIELDS)
