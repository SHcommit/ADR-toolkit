# Task 5 Report: Optional Supersession Fields

## Status

Implemented validation for optional `supersedes` and `superseded_by`
frontmatter fields, and kept the documented JSON Schema in sync.

## Files

- `skills/adr-toolkit/scripts/core/schema.py`
- `skills/adr-toolkit/schemas/adr.schema.json`
- `tests/unit/test_schema.py`

## Test Evidence

### RED

Command: `python3 -m pytest tests/unit/test_schema.py -v`

Result: 1 failed, 10 passed. The intended failure was
`test_optional_supersedes_field_wrong_type_is_reported`: a string
`supersedes` value was silently accepted before optional-field validation
existed.

### GREEN

Command: `python3 -m pytest tests/unit/test_schema.py -v`

Result: 11 passed.

### Full Suite

Command: `python3 -m pytest tests/unit tests/integration -v`

Result: 90 passed.

## JSON Schema Parity Invariant

The structured parity test parses `schemas/adr.schema.json` and asserts:

1. The JSON Schema `required` field set exactly equals `schema.REQUIRED_FIELDS`.
2. Every field in `schema.REQUIRED_FIELDS` and `schema.OPTIONAL_FIELDS`
   exists in JSON Schema `properties`.
3. Every such property has the matching top-level JSON type:
   `str` to `string`, `list` to `array`, and `bool` to `boolean`.

The required-set equality also ensures optional runtime fields are not added to
JSON Schema `required`.

## Self-Review

- Optional fields are validated only when present; their absence remains valid.
- `supersedes` accepts a list and rejects a scalar string.
- `superseded_by` accepts a string.
- The JSON Schema exposes both fields without making either required.
- The parity test reads and parses JSON instead of inspecting source text.

## Concerns

Parity intentionally covers the requested top-level field/type contract. It
does not compare nested JSON Schema constraints such as array item types, which
remain outside Task 5's runtime validation scope.
