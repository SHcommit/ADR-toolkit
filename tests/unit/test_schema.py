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
