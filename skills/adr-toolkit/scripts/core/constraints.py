"""Extract structured `constraints:` rules from an ADR body's fenced block.

Not a general YAML parser — supports exactly the fixed shape the design
spec defines (§7, §16.2): a top-level `constraints:` list of mappings with
a small set of known fields, list-valued fields written as a JSON-style
array on one line. Mirrors core/frontmatter.py's hand-rolled-subset
approach rather than adding a YAML dependency.
"""
import json
import re

FENCE_RE = re.compile(r"```ya?ml\n(.*?)\n```", re.DOTALL)

KNOWN_FIELDS = {"id", "kind", "paths", "pattern", "severity", "message"}
LIST_FIELDS = {"paths", "pattern"}


class ConstraintsError(ValueError):
    pass


def extract_constraints(body: str) -> list:
    rules = []
    for fence_match in FENCE_RE.finditer(body):
        lines = fence_match.group(1).splitlines()
        if not lines or not lines[0].strip().startswith("constraints:"):
            continue
        rules.extend(_parse_rules(lines[1:]))
    return rules


def _parse_rules(lines) -> list:
    rules = []
    current = None
    for raw_line in lines:
        if not raw_line.strip():
            continue
        if raw_line.startswith("  - "):
            if current is not None:
                rules.append(current)
            current = {}

        stripped = raw_line.strip()
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()

        if ":" not in stripped:
            raise ConstraintsError(f"Malformed constraints line: {raw_line!r}")
        key, _, value = stripped.partition(":")
        key, value = key.strip(), value.strip()

        if current is None:
            raise ConstraintsError(f"Constraints field with no preceding '- ': {raw_line!r}")
        if key not in KNOWN_FIELDS:
            raise ConstraintsError(f"Unknown constraints field: {key!r}")

        if key in LIST_FIELDS:
            try:
                parsed_value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ConstraintsError(f"Field {key!r} must be a JSON-style list, got {value!r}") from exc
            if not isinstance(parsed_value, list):
                raise ConstraintsError(f"Field {key!r} must be a list, got {value!r}")
            current[key] = parsed_value
        else:
            current[key] = value.strip('"').strip("'")

    if current is not None:
        rules.append(current)
    return rules
