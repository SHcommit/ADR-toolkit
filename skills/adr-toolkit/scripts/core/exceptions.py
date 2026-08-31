"""Structural validation and matching for CHECK policy exceptions.

schemas/exception.schema.json documents the same shape for external tools;
this module is the version actually enforced at runtime.
"""
from datetime import date as date_cls
import re

from scripts.core import globs

REQUIRED_FIELDS = {
    "id": str,
    "adr_id": str,
    "rule_id": str,
    "owner": str,
    "reason": str,
    "scope": list,
    "expiry": str,
    "created": str,
}

ID_RE = re.compile(r"^EXC-\d{4}$")
ADR_ID_RE = re.compile(r"^ADR-\d{4}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_date(field: str, value: str, errors: list) -> None:
    if not DATE_RE.match(value):
        errors.append(f"{field} {value!r} is not YYYY-MM-DD")
        return
    year, month, day = (int(part) for part in value.split("-"))
    try:
        date_cls(year, month, day)
    except ValueError:
        errors.append(f"{field} {value!r} is not a real calendar date")


def validate_exception(data: dict) -> list:
    errors = []
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in data:
            errors.append(f"missing required field: {field}")
            continue
        if not isinstance(data[field], expected_type):
            errors.append(
                f"field {field!r} must be {expected_type.__name__}, "
                f"got {type(data[field]).__name__}"
            )

    if isinstance(data.get("id"), str) and not ID_RE.match(data["id"]):
        errors.append(f"id {data['id']!r} does not match EXC-NNNN")

    if isinstance(data.get("adr_id"), str) and not ADR_ID_RE.match(data["adr_id"]):
        errors.append(f"adr_id {data['adr_id']!r} does not match ADR-NNNN")

    for field in ("owner", "reason", "rule_id"):
        if isinstance(data.get(field), str) and not data[field].strip():
            errors.append(f"{field} must not be empty")

    if isinstance(data.get("scope"), list) and not data["scope"]:
        errors.append("scope must contain at least one path pattern")

    if isinstance(data.get("expiry"), str):
        _validate_date("expiry", data["expiry"], errors)
    if isinstance(data.get("created"), str):
        _validate_date("created", data["created"], errors)

    return errors


def is_expired(expiry: str, today: date_cls) -> bool:
    year, month, day = (int(part) for part in expiry.split("-"))
    return today > date_cls(year, month, day)


def applies_to(exception: dict, *, adr_id: str, rule_id: str, file_path: str) -> bool:
    if exception.get("adr_id") != adr_id or exception.get("rule_id") != rule_id:
        return False
    if file_path is None:
        return False
    return any(globs.match(pattern, file_path) for pattern in exception.get("scope", []))
