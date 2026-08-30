"""Pure structural constraint matching for CHECK (§16.2).

No file or git I/O — callers pass in an already-parsed diff (Task 3's
diff.py `files` list) and the set of paths that exist in the working tree
after the diff. The six constraints: rule kinds collapse into four
mechanisms here; which kind maps to which mechanism is fixed by the design
spec, not configurable.
"""
import re

from scripts.core import globs

CONTENT_PATTERN_KINDS = {"forbidden_import", "dependency_forbidden"}
REQUIRED_PATH_KINDS = {"required_path"}
FORBIDDEN_PATH_KINDS = {"forbidden_path"}
EXISTENCE_KINDS = {"file_must_exist", "test_must_exist"}


def evaluate_rule(rule: dict, diff_files: list, existing_paths: set):
    kind = rule.get("kind")
    if kind in CONTENT_PATTERN_KINDS:
        return _content_pattern(rule, diff_files)
    if kind in REQUIRED_PATH_KINDS:
        return _required_companion_path(rule, diff_files, existing_paths)
    if kind in FORBIDDEN_PATH_KINDS:
        return _forbidden_companion_path(rule, diff_files)
    if kind in EXISTENCE_KINDS:
        return _existence_check(rule, existing_paths)
    return None


def _as_list(value) -> list:
    # core/frontmatter.py's hand-rolled YAML subset yields a bare string for
    # `affected_paths: src/features/` and a bool for `affected_paths: false`.
    # Iterating either one here would be wrong (a string iterates *characters*,
    # so "s" would "overlap" setup.py) or fatal (a bool raises TypeError and
    # aborts the whole check run), so normalize at the shared entry point.
    return value if isinstance(value, list) else []


def affected_paths_overlap(diff_files: list, affected_paths) -> bool:
    touched = _touched_paths(diff_files)
    return any(
        globs.path_under(diff_path, ap) or globs.match(ap, diff_path)
        for diff_path in touched
        for ap in _as_list(affected_paths)
        if isinstance(ap, str)
    )


def _touched_paths(diff_files: list) -> set:
    return {f["path"] for f in diff_files}


def _files_matching(diff_files: list, path_patterns: list) -> list:
    return [f for f in diff_files if any(globs.match(p, f["path"]) for p in path_patterns)]


def _content_pattern(rule: dict, diff_files: list):
    regexes = [re.compile(p) for p in rule.get("pattern", [])]
    for file_entry in _files_matching(diff_files, rule.get("paths", [])):
        for line in file_entry.get("added_lines", []):
            for regex in regexes:
                if regex.search(line):
                    return _violation(rule, file=file_entry["path"], evidence={"line": line, "pattern": regex.pattern})
    return None


def _required_companion_path(rule: dict, diff_files: list, existing_paths: set):
    trigger_files = _files_matching(diff_files, rule.get("paths", []))
    if not trigger_files:
        return None
    companion_patterns = rule.get("pattern", [])
    candidates = _touched_paths(diff_files) | existing_paths
    if any(globs.match(cp, path) for cp in companion_patterns for path in candidates):
        return None
    return _violation(rule, file=trigger_files[0]["path"], evidence={"missing_companion": companion_patterns})


def _forbidden_companion_path(rule: dict, diff_files: list):
    trigger_files = _files_matching(diff_files, rule.get("paths", []))
    if not trigger_files:
        return None
    companion_patterns = rule.get("pattern", [])
    touched = _touched_paths(diff_files)
    hits = sorted(p for p in touched if any(globs.match(cp, p) for cp in companion_patterns))
    if not hits:
        return None
    return _violation(rule, file=trigger_files[0]["path"], evidence={"forbidden_companion": hits})


def _existence_check(rule: dict, existing_paths: set):
    required_patterns = rule.get("paths", [])
    if any(globs.match(p, path) for p in required_patterns for path in existing_paths):
        return None
    return _violation(rule, file=None, evidence={"missing_paths": required_patterns})


def _violation(rule: dict, *, file, evidence) -> dict:
    return {
        "rule_id": rule.get("id"),
        "kind": "verified_violation",
        "severity": rule.get("severity", "major"),
        "message": rule.get("message", ""),
        "file": file,
        "evidence": evidence,
    }
