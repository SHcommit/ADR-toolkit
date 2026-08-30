from datetime import date

from scripts.core.exceptions import applies_to, is_expired, validate_exception

VALID = {
    "id": "EXC-0001",
    "adr_id": "ADR-0001",
    "rule_id": "no-provider-sdk-in-feature",
    "owner": "YangSeungHyun",
    "reason": "Vendor migration is in progress; tracked in issue #42.",
    "scope": ["src/features/legacy/**"],
    "expiry": "2026-12-31",
    "created": "2026-08-30",
}


def test_valid_exception_has_no_errors():
    assert validate_exception(VALID) == []


def test_missing_required_field_is_reported():
    data = {k: v for k, v in VALID.items() if k != "owner"}
    errors = validate_exception(data)
    assert any("owner" in e for e in errors)


def test_empty_owner_is_rejected():
    data = {**VALID, "owner": "  "}
    errors = validate_exception(data)
    assert any("owner" in e for e in errors)


def test_empty_scope_list_is_rejected():
    data = {**VALID, "scope": []}
    errors = validate_exception(data)
    assert any("scope" in e for e in errors)


def test_malformed_expiry_is_rejected():
    data = {**VALID, "expiry": "12/31/2026"}
    errors = validate_exception(data)
    assert any("expiry" in e for e in errors)


def test_malformed_id_is_rejected():
    data = {**VALID, "id": "exception-1"}
    errors = validate_exception(data)
    assert any("id" in e for e in errors)


def test_malformed_adr_id_is_rejected():
    data = {**VALID, "adr_id": "1"}
    errors = validate_exception(data)
    assert any("adr_id" in e for e in errors)


def test_is_expired_true_after_expiry_date():
    assert is_expired("2026-01-01", today=date(2026, 1, 2)) is True


def test_is_expired_false_on_expiry_date():
    assert is_expired("2026-01-01", today=date(2026, 1, 1)) is False


def test_is_expired_false_before_expiry_date():
    assert is_expired("2026-01-01", today=date(2025, 12, 31)) is False


def test_applies_to_matches_adr_rule_and_scope():
    assert applies_to(
        VALID, adr_id="ADR-0001", rule_id="no-provider-sdk-in-feature",
        file_path="src/features/legacy/old.py",
    ) is True


def test_applies_to_false_when_adr_id_differs():
    assert applies_to(
        VALID, adr_id="ADR-0002", rule_id="no-provider-sdk-in-feature",
        file_path="src/features/legacy/old.py",
    ) is False


def test_applies_to_false_when_rule_id_differs():
    assert applies_to(
        VALID, adr_id="ADR-0001", rule_id="some-other-rule",
        file_path="src/features/legacy/old.py",
    ) is False


def test_applies_to_false_when_file_outside_scope():
    assert applies_to(
        VALID, adr_id="ADR-0001", rule_id="no-provider-sdk-in-feature",
        file_path="src/features/current/new.py",
    ) is False
