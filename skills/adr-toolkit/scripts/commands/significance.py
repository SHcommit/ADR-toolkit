"""Deterministic CLI wrapper around scripts.rules.significance."""
import json
from pathlib import Path

from scripts.rules import significance


def run(args) -> dict:
    try:
        raw_input = Path(args.input).read_text(encoding="utf-8")
    except FileNotFoundError:
        return {
            "ok": False,
            "operation": "significance",
            "errors": [{"code": "INPUT_FILE_NOT_FOUND", "path": args.input}],
        }

    try:
        criteria_scores = json.loads(raw_input)
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "operation": "significance",
            "errors": [{"code": "INPUT_FILE_INVALID_JSON", "path": args.input, "detail": str(exc)}],
        }

    try:
        total = significance.score(criteria_scores)
    except ValueError as exc:
        return {
            "ok": False,
            "operation": "significance",
            "errors": [{"code": "INVALID_SCORE", "detail": str(exc)}],
        }

    return {
        "ok": True,
        "operation": "significance",
        "total": total,
        "classification": significance.classify(total),
    }
