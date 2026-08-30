import pytest

from scripts.core.constraints import ConstraintsError, extract_constraints

BODY_WITH_CONSTRAINTS = """# Use a provider port

## Implementation Constraints

Feature modules must go through the LLM port, never call a provider SDK
directly.

```yaml
constraints:
  - id: no-provider-sdk-in-feature
    kind: forbidden_import
    paths: ["src/features/**"]
    pattern: ["openai", "anthropic"]
    severity: major
    message: "Feature modules must use the LLM port."
  - id: registry-required
    kind: required_path
    paths: ["src/events/**"]
    pattern: ["src/events/registry.py"]
    severity: minor
    message: "New event types must be registered."
```
"""

BODY_WITHOUT_CONSTRAINTS = "# Use a provider port\n\nNo fenced block here.\n"

BODY_WITH_MALFORMED_CONSTRAINTS = """# Bad ADR

```yaml
constraints:
  - id: broken
    kind forbidden_import
```
"""


def test_extracts_all_rules_with_correct_fields():
    rules = extract_constraints(BODY_WITH_CONSTRAINTS)
    assert len(rules) == 2
    assert rules[0]["id"] == "no-provider-sdk-in-feature"
    assert rules[0]["kind"] == "forbidden_import"
    assert rules[0]["paths"] == ["src/features/**"]
    assert rules[0]["pattern"] == ["openai", "anthropic"]
    assert rules[0]["severity"] == "major"
    assert rules[1]["id"] == "registry-required"
    assert rules[1]["kind"] == "required_path"


def test_no_fenced_block_returns_empty_list():
    assert extract_constraints(BODY_WITHOUT_CONSTRAINTS) == []


def test_malformed_line_raises_constraints_error():
    with pytest.raises(ConstraintsError):
        extract_constraints(BODY_WITH_MALFORMED_CONSTRAINTS)


BODY_WITH_UNKNOWN_KIND = """
## Implementation Constraints

```yaml
constraints:
  - id: typo-kind
    kind: forbidden_imports
    paths: ["src/features/**"]
    pattern: ["openai"]
    severity: major
    message: "typo'd kind"
```
"""


def test_unknown_kind_raises_constraints_error():
    with pytest.raises(ConstraintsError) as exc:
        extract_constraints(BODY_WITH_UNKNOWN_KIND)
    assert "forbidden_imports" in str(exc.value)


def test_all_six_known_kinds_are_accepted():
    for kind in [
        "forbidden_import", "dependency_forbidden", "required_path",
        "forbidden_path", "file_must_exist", "test_must_exist",
    ]:
        body = (
            "```yaml\nconstraints:\n"
            f"  - id: r\n    kind: {kind}\n    paths: [\"src/**\"]\n"
            "    severity: major\n    message: \"m\"\n```\n"
        )
        assert extract_constraints(body)[0]["kind"] == kind
