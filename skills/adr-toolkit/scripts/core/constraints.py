"""Extract structured `constraints:` rules from an ADR body's fenced block.

Not a general YAML parser — supports exactly the fixed shape the design
spec defines (§7, §16.2): a top-level `constraints:` list of mappings with
a small set of known fields, list-valued fields written as a JSON-style
array on one line. Mirrors core/frontmatter.py's hand-rolled-subset
approach rather than adding a YAML dependency.
"""
import json
import re

from scripts.core.errors import AdrToolkitError

FENCE_RE = re.compile(r"```ya?ml\n(.*?)\n```", re.DOTALL)

KNOWN_FIELDS = {"id", "kind", "paths", "pattern", "severity", "message"}
LIST_FIELDS = {"paths", "pattern"}
# An unrecognized `kind` is silently unenforced downstream (conflict.evaluate_rule
# returns None for it), and CHECK would then report the ADR as "related" — i.e.
# "evaluated, nothing fired" — which is a lie. Reject it at parse time so it
# surfaces through check.py's existing BAD_CONSTRAINTS warning path instead.
KNOWN_KINDS = {
    "forbidden_import",
    "dependency_forbidden",
    "required_path",
    "forbidden_path",
    "file_must_exist",
    "test_must_exist",
}

# Only these two kinds ever pass their `pattern` values to re.compile() as
# regex (rules/conflict.py::_content_pattern) -- required_path/forbidden_path
# treat `pattern` as glob syntax via core/globs.py instead, which is built
# from a fixed, safe translation and can't produce catastrophic
# backtracking. Kept as a small local set rather than importing
# rules/conflict.py's CONTENT_PATTERN_KINDS, since core/ must not depend on
# rules/ (the opposite direction already holds throughout this codebase).
_REGEX_PATTERN_KINDS = {"forbidden_import", "dependency_forbidden"}

# A quantified group whose own body ends in a quantifier -- e.g. (a+)+,
# (a*)*, (x{1,3})+ -- is the single most common shape behind catastrophic
# regex backtracking (ReDoS). This is a static, string-level heuristic, not
# a full ReDoS detector: alternation-based patterns like (a|a)* are a
# different dangerous shape and are not caught here. It exists because the
# runtime SIGALRM-based timeout guard in rules/conflict.py is POSIX-only;
# rejecting the pattern here, before it is ever compiled or executed,
# protects Windows too (docs/adr-toolkit-audit-report.md §2.2 2.3).
_QUANTIFIER = r"(?:[+*]|\{\d*,?\d*\})"
_NESTED_QUANTIFIER_RE = re.compile(r"\([^()]*" + _QUANTIFIER + r"\)" + _QUANTIFIER)


class ConstraintsError(AdrToolkitError):
    error_code = "BAD_CONSTRAINTS"


def lint(body: str) -> list:
    """Best-effort pre-flight check for a malformed constraints: block, so a
    typo surfaces at CREATE/STATUS time instead of silently going
    unenforced until CHECK runs against it later
    (docs/adr-toolkit-audit-report.md §2.5 5.2)."""
    try:
        extract_constraints(body)
    except ConstraintsError as exc:
        return [{"code": "BAD_CONSTRAINTS", "detail": str(exc)}]
    return []


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
            parsed_value = value.strip('"').strip("'")
            if key == "kind" and parsed_value not in KNOWN_KINDS:
                raise ConstraintsError(
                    f"Unknown constraints kind: {parsed_value!r} "
                    f"(known kinds: {', '.join(sorted(KNOWN_KINDS))})"
                )
            current[key] = parsed_value

    if current is not None:
        rules.append(current)

    for rule in rules:
        if rule.get("kind") in _REGEX_PATTERN_KINDS:
            for pattern in rule.get("pattern", []):
                _reject_if_redos_prone(pattern)

    return rules


def _reject_if_redos_prone(pattern: str) -> None:
    if _NESTED_QUANTIFIER_RE.search(pattern):
        raise ConstraintsError(
            f"pattern {pattern!r} has a nested quantifier and risks catastrophic "
            f"backtracking (ReDoS) -- rewrite it without a repeated group inside "
            f"another repeated group"
        )
