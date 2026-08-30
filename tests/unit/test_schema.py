import json
from pathlib import Path

from scripts.core import schema
from scripts.core.locale import SUPPORTED_LOCALES
from scripts.core.schema import validate_frontmatter

VALID = {
    "id": "ADR-0001",
    "title": "Record architecture decisions",
    "status": "accepted",
    "date": "2026-08-29",
    "decision_makers": [],
    "related": [],
    "affected_paths": ["docs/decisions/"],
    "tags": ["process"],
    "retrospective": False,
}


def test_valid_frontmatter_has_no_errors():
    assert validate_frontmatter(VALID) == []


def test_missing_field_is_reported():
    data = dict(VALID)
    del data["status"]
    errors = validate_frontmatter(data)
    assert any("status" in e for e in errors)


def test_bad_id_format_is_reported():
    data = dict(VALID, id="0001")
    errors = validate_frontmatter(data)
    assert any("id" in e for e in errors)


def test_unknown_status_is_reported():
    data = dict(VALID, status="archived")
    errors = validate_frontmatter(data)
    assert any("status" in e for e in errors)


def test_bad_date_format_is_reported():
    data = dict(VALID, date="29-08-2026")
    errors = validate_frontmatter(data)
    assert any("date" in e for e in errors)


def test_wrong_type_is_reported():
    data = dict(VALID, tags="process")  # should be a list
    errors = validate_frontmatter(data)
    assert any("tags" in e for e in errors)


def test_optional_supersedes_field_is_allowed_when_a_list():
    data = dict(VALID, supersedes=["ADR-0002"])
    assert validate_frontmatter(data) == []


def test_optional_supersedes_field_wrong_type_is_reported():
    data = dict(VALID, supersedes="ADR-0002")  # should be a list
    errors = validate_frontmatter(data)
    assert any("supersedes" in error for error in errors)


def test_optional_superseded_by_field_is_allowed_when_a_string():
    data = dict(VALID, superseded_by="ADR-0009")
    assert validate_frontmatter(data) == []


def test_absence_of_optional_fields_is_not_an_error():
    assert validate_frontmatter(VALID) == []


def test_optional_locale_is_valid_and_unknown_locale_is_rejected():
    assert validate_frontmatter({**VALID, "locale": "ko"}) == []
    errors = validate_frontmatter({**VALID, "locale": "xx"})
    assert any("locale" in error for error in errors)


def test_json_schema_matches_runtime_frontmatter_fields():
    schema_path = Path(__file__).parents[2] / "skills/adr-toolkit/schemas/adr.schema.json"
    with schema_path.open() as schema_file:
        json_schema = json.load(schema_file)

    expected_json_types = {str: "string", list: "array", bool: "boolean"}
    runtime_fields = {
        **schema.REQUIRED_FIELDS,
        **schema.OPTIONAL_FIELDS,
    }

    assert set(json_schema["required"]) == set(schema.REQUIRED_FIELDS)
    for field, python_type in runtime_fields.items():
        assert field in json_schema["properties"]
        assert json_schema["properties"][field]["type"] == expected_json_types[python_type]

    assert "locale" not in json_schema["required"]
    assert tuple(json_schema["properties"]["locale"]["enum"]) == SUPPORTED_LOCALES
