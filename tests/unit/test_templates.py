# tests/unit/test_templates.py
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit" / "templates"

REQUIRED_MINIMAL_SECTIONS = [
    "## Context and Problem Statement",
    "## Considered Options",
    "## Decision Outcome",
    "## Consequences",
    "## Confirmation",
    "## Revisit Triggers",
]

REQUIRED_FULL_SECTIONS = REQUIRED_MINIMAL_SECTIONS + [
    "## Decision Drivers",
    "## Pros and Cons of the Options",
]


def test_minimal_template_has_required_sections():
    text = (TEMPLATES / "madr-minimal.md").read_text(encoding="utf-8")
    for section in REQUIRED_MINIMAL_SECTIONS:
        assert section in text, f"missing {section}"


def test_full_template_has_required_sections():
    text = (TEMPLATES / "madr-full.md").read_text(encoding="utf-8")
    for section in REQUIRED_FULL_SECTIONS:
        assert section in text, f"missing {section}"
