# tests/unit/test_conflict.py
from scripts.rules import conflict

DIFF_FILES = [
    {"path": "src/features/x.py", "change_type": "modified",
     "added_lines": ["import openai", "def handler(): pass"], "removed_lines": []},
    {"path": "src/events/producer.py", "change_type": "added",
     "added_lines": ["class Producer: pass"], "removed_lines": []},
]


def test_content_pattern_fires_on_matching_added_line():
    rule = {"id": "no-sdk", "kind": "forbidden_import", "paths": ["src/features/**"],
            "pattern": ["openai"], "severity": "major", "message": "no direct SDK"}
    result = conflict.evaluate_rule(rule, DIFF_FILES, set())
    assert result["kind"] == "verified_violation"
    assert result["rule_id"] == "no-sdk"
    assert result["file"] == "src/features/x.py"


def test_content_pattern_does_not_fire_without_a_match():
    rule = {"id": "no-sdk", "kind": "forbidden_import", "paths": ["src/features/**"],
            "pattern": ["anthropic"], "severity": "major", "message": "no direct SDK"}
    assert conflict.evaluate_rule(rule, DIFF_FILES, set()) is None


def test_required_companion_path_fires_when_companion_missing():
    rule = {"id": "registry", "kind": "required_path", "paths": ["src/events/**"],
            "pattern": ["src/events/registry.py"], "severity": "minor", "message": "register it"}
    result = conflict.evaluate_rule(rule, DIFF_FILES, set())
    assert result["kind"] == "verified_violation"


def test_required_companion_path_satisfied_by_existing_paths():
    rule = {"id": "registry", "kind": "required_path", "paths": ["src/events/**"],
            "pattern": ["src/events/registry.py"], "severity": "minor", "message": "register it"}
    result = conflict.evaluate_rule(rule, DIFF_FILES, {"src/events/registry.py"})
    assert result is None


def test_forbidden_companion_path_fires_when_both_touched():
    rule = {"id": "no-db-in-features", "kind": "forbidden_path", "paths": ["src/features/**"],
            "pattern": ["src/events/**"], "severity": "major", "message": "boundary violation"}
    result = conflict.evaluate_rule(rule, DIFF_FILES, set())
    assert result["kind"] == "verified_violation"


def test_forbidden_companion_path_does_not_fire_when_companion_absent():
    rule = {"id": "no-db-in-features", "kind": "forbidden_path", "paths": ["src/features/**"],
            "pattern": ["src/db/**"], "severity": "major", "message": "boundary violation"}
    assert conflict.evaluate_rule(rule, DIFF_FILES, set()) is None


def test_existence_check_fires_when_path_missing():
    rule = {"id": "must-exist", "kind": "file_must_exist", "paths": ["src/events/registry.py"],
            "severity": "major", "message": "registry must exist"}
    assert conflict.evaluate_rule(rule, DIFF_FILES, set())["kind"] == "verified_violation"


def test_existence_check_satisfied_when_path_present():
    rule = {"id": "must-exist", "kind": "test_must_exist", "paths": ["tests/test_x.py"],
            "severity": "major", "message": "tests must exist"}
    assert conflict.evaluate_rule(rule, DIFF_FILES, {"tests/test_x.py"}) is None


def test_unknown_kind_produces_no_finding():
    rule = {"id": "mystery", "kind": "not_a_real_kind", "paths": ["src/**"]}
    assert conflict.evaluate_rule(rule, DIFF_FILES, set()) is None


def test_affected_paths_overlap_matches_directory_prefix():
    assert conflict.affected_paths_overlap(DIFF_FILES, ["src/features/"])


def test_affected_paths_overlap_matches_glob():
    assert conflict.affected_paths_overlap(DIFF_FILES, ["src/events/**"])


def test_affected_paths_overlap_false_when_no_match():
    assert not conflict.affected_paths_overlap(DIFF_FILES, ["src/unrelated/"])
