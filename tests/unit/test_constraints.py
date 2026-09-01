import json

import pytest

from scripts.core.constraints import ConstraintsError, extract_constraints, lint

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


def test_lint_returns_no_warnings_for_a_valid_body():
    assert lint(BODY_WITH_CONSTRAINTS) == []


def test_lint_returns_no_warnings_for_a_body_with_no_constraints_block():
    assert lint("# Just prose\n\nNo constraints here.\n") == []


def test_lint_returns_a_bad_constraints_warning_for_a_malformed_block():
    warnings = lint(BODY_WITH_UNKNOWN_KIND)
    assert warnings == [{"code": "BAD_CONSTRAINTS", "detail": warnings[0]["detail"]}]
    assert "forbidden_imports" in warnings[0]["detail"]


def _body_with_pattern(kind: str, pattern: list) -> str:
    return (
        "```yaml\nconstraints:\n"
        f"  - id: r\n    kind: {kind}\n    paths: [\"src/**\"]\n"
        f"    pattern: {json.dumps(pattern)}\n"
        "    severity: major\n    message: \"m\"\n```\n"
    )


@pytest.mark.parametrize("dangerous_pattern", [
    r"(a+)+$",
    r"(a*)*",
    r"(a+)*",
    r"((a+)+)+",
    r"(x{1,3})+",
])
def test_nested_quantifier_pattern_is_rejected_for_content_pattern_kinds(dangerous_pattern):
    for kind in ("forbidden_import", "dependency_forbidden"):
        with pytest.raises(ConstraintsError) as exc:
            extract_constraints(_body_with_pattern(kind, [dangerous_pattern]))
        assert "nested quantifier" in str(exc.value)


def test_nested_quantifier_check_never_actually_runs_the_pattern(monkeypatch):
    # The whole point is that a dangerous pattern is rejected by inspecting
    # the pattern *string* -- it must never reach re.compile()/re.search(),
    # which is what makes this protection work identically without a
    # runtime timeout (i.e. on Windows, where signal.SIGALRM doesn't exist).
    import re as re_module

    def _boom(*args, **kwargs):
        raise AssertionError("a rejected pattern must never be compiled")

    monkeypatch.setattr(re_module, "compile", _boom)

    with pytest.raises(ConstraintsError):
        extract_constraints(_body_with_pattern("forbidden_import", ["(a+)+"]))


def test_ordinary_patterns_are_not_flagged_as_dangerous():
    body = _body_with_pattern("forbidden_import", ["openai", "anthropic", "^foo.*bar$"])
    rules = extract_constraints(body)
    assert rules[0]["pattern"] == ["openai", "anthropic", "^foo.*bar$"]


def test_nested_quantifier_in_a_non_regex_kind_is_not_rejected():
    # required_path/forbidden_path treat `pattern` as glob syntax (via
    # core/globs.py), which can't produce catastrophic backtracking --
    # only forbidden_import/dependency_forbidden compile it as regex.
    body = _body_with_pattern("required_path", ["src/(a+)+/registry.py"])
    rules = extract_constraints(body)
    assert rules[0]["pattern"] == ["src/(a+)+/registry.py"]


def test_lint_reports_nested_quantifier_as_bad_constraints_warning():
    warnings = lint(_body_with_pattern("forbidden_import", ["(a+)+"]))
    assert warnings[0]["code"] == "BAD_CONSTRAINTS"
    assert "nested quantifier" in warnings[0]["detail"]
