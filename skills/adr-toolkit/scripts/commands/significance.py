"""Deterministic CLI wrapper around scripts.rules.significance."""
import json
from pathlib import Path

from scripts.rules import significance


def run(args) -> dict:
    criteria_scores = json.loads(Path(args.input).read_text(encoding="utf-8"))

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
