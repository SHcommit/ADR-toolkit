"""Structural validation for ADR frontmatter.

schemas/adr.schema.json documents the same shape for external tools; this
module is the version actually enforced at runtime.
"""
from datetime import date as date_cls
import re

from scripts.core.lifecycle import STATUSES

REQUIRED_FIELDS = {
    "id": str,
    "title": str,
    "status": str,
    "date": str,
    "decision_makers": list,
    "related": list,
    "affected_paths": list,
    "tags": list,
    "retrospective": bool,
}

ID_RE = re.compile(r"^ADR-\d{4}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_frontmatter(data: dict) -> list:
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
        errors.append(f"id {data['id']!r} does not match ADR-NNNN")

    if "status" in data and data["status"] not in STATUSES:
        errors.append(f"status {data['status']!r} is not one of {sorted(STATUSES)}")

    if isinstance(data.get("date"), str):
        if not DATE_RE.match(data["date"]):
            errors.append(f"date {data['date']!r} is not YYYY-MM-DD")
        else:
            year, month, day = (int(part) for part in data["date"].split("-"))
            try:
                date_cls(year, month, day)
            except ValueError:
                errors.append(f"date {data['date']!r} is not a real calendar date")

    return errors
