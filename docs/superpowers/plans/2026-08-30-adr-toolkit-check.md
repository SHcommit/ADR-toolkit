# ADR Toolkit — CHECK (Plan 3 of 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the CHECK workflow — a `diff` command that wraps `git diff` for three range modes, and a `check` command that matches a diff against Accepted ADRs' structured `constraints:` rules and Superseded ADRs' `affected_paths`, producing a four-way classified finding report with five resolution options on every verified violation.

**Architecture:** Four new deterministic layers, each independently testable: `core/globs.py` (a `**`-aware glob matcher, stdlib-only since `fnmatch`/`PurePath.match` don't handle `**`), `core/constraints.py` (extracts the fenced `constraints:` YAML block from an ADR body — a small fixed-shape parser, not a general YAML parser, mirroring `core/frontmatter.py`'s hand-rolled-subset precedent), `scripts/rules/conflict.py` (pure functions implementing the four matching mechanisms the six `constraints:` rule kinds collapse into, mirroring `scripts/rules/significance.py`'s no-I/O style), and `scripts/commands/{diff,check}.py` (the two new CLI commands — `diff` shells out to git, `check` orchestrates everything else). `SKILL.md` gains a CHECK section describing how the agent runs `check` and presents the five resolution options; no conflict-detection judgment is hardcoded in Python beyond the six structural rule kinds.

**Tech Stack:** Same as Plans 1–2 — Python 3.9+ standard library only (including `subprocess` for git, `re`, `json`), pytest.

**Spec:** `docs/superpowers/specs/2026-08-29-adr-toolkit-design.md` (§6 ADR document format, §7 CHECK scope, §11 CHECK workflow data flow, §16 Plan 3 implementation decisions)

## Global Constraints

- Same as Plans 1–2: Python 3.9+ stdlib only; UTF-8 explicit; no `shell=True`; command modules never `print()`; avoid `X | None` union syntax, use `typing.Optional`.
- `diff`/`check` never write any file — CHECK is read-only by design (§7); no `--dry-run` flag is needed because there is nothing to preview before writing.
- `git` is invoked only via `subprocess.run` with argument lists (`["git", "-C", str(root), ...]`), never `shell=True`, never a string-interpolated command.
- `constraints:` rules are evaluated only against ADRs with `status: accepted` (§16.4); superseded ADRs are handled by the separate superseded-reference pass, never by re-running their old `constraints:` block.
- Malformed ADR frontmatter or a malformed `constraints:` block is caught per-file/per-ADR and degrades to a `warnings` entry — `check` never aborts because one ADR is broken, matching the pattern the Plan 2 closeout review established in `related.py`/`status.py`/`supersede.py`.
- A `diff` failure (not a git repo, unknown ref) returns a specific error code (`NOT_A_GIT_REPO`, `INVALID_REF`, `GIT_DIFF_FAILED`) — never a raw `subprocess` traceback surfaced through `adr.py main()`'s `INTERNAL_ERROR` fallback.
- Out of scope for this plan (tracked in `project-roadmap.md` / Plan 4): i18n wiring, Codex/Gemini CLI/Antigravity CLI adapters, release automation, full semantic/AST conflict detection.
- Every task must leave `python -m pytest tests/unit tests/integration -v` green before its commit step.

---

### Task 1: `core/globs.py` — a `**`-aware glob matcher

**Files:**
- Create: `skills/adr-toolkit/scripts/core/globs.py`
- Test: `tests/unit/test_globs.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `match(pattern: str, path: str) -> bool`. Used by Task 4 (`rules/conflict.py`).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_globs.py
from scripts.core import globs


def test_exact_match():
    assert globs.match("src/events/producer.py", "src/events/producer.py")
    assert not globs.match("src/events/producer.py", "src/events/consumer.py")


def test_single_star_matches_within_one_segment():
    assert globs.match("src/events/*.py", "src/events/producer.py")
    assert not globs.match("src/events/*.py", "src/events/sub/producer.py")


def test_double_star_matches_across_segments():
    assert globs.match("src/features/**", "src/features/x.py")
    assert globs.match("src/features/**", "src/features/sub/y.py")
    assert not globs.match("src/features/**", "src/other/x.py")


def test_double_star_prefix_matches_any_depth():
    assert globs.match("**/test_*.py", "test_foo.py")
    assert globs.match("**/test_*.py", "src/deep/test_foo.py")
    assert not globs.match("**/test_*.py", "src/deep/foo_test.py")


def test_question_mark_matches_single_character():
    assert globs.match("src/adr-?.md", "src/adr-1.md")
    assert not globs.match("src/adr-?.md", "src/adr-10.md")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_globs.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/core/globs.py
"""A **-aware glob matcher, stdlib-only.

Python's fnmatch/PurePath.match don't treat ** as "any number of path
segments" the way ArchUnit-style path rules need, so this implements just
that one extension on top of literal/*/? matching.
"""
import re


def match(pattern: str, path: str) -> bool:
    return re.match(_translate(pattern), path) is not None


def _translate(pattern: str) -> str:
    parts = []
    i, n = 0, len(pattern)
    while i < n:
        char = pattern[i]
        if pattern[i:i + 2] == "**":
            if i + 2 < n and pattern[i + 2] == "/":
                parts.append(r"(?:.*/)?")
                i += 3
            else:
                parts.append(r".*")
                i += 2
        elif char == "*":
            parts.append(r"[^/]*")
            i += 1
        elif char == "?":
            parts.append(r"[^/]")
            i += 1
        else:
            parts.append(re.escape(char))
            i += 1
    return "^" + "".join(parts) + "$"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_globs.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/core/globs.py tests/unit/test_globs.py
git commit -m "feat: add **-aware glob matcher for constraint path patterns"
```

---

### Task 2: `core/constraints.py` — extract `constraints:` rules from an ADR body

**Files:**
- Create: `skills/adr-toolkit/scripts/core/constraints.py`
- Test: `tests/unit/test_constraints.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `extract_constraints(body: str) -> list`, `ConstraintsError(ValueError)`. Used by Task 6 (`check.py`).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_constraints.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_constraints.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/core/constraints.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_constraints.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/core/constraints.py tests/unit/test_constraints.py
git commit -m "feat: extract constraints: rules from an ADR body's fenced block"
```

---

### Task 3: `commands/diff.py` — git diff wrapper + CLI wiring

**Files:**
- Create: `skills/adr-toolkit/scripts/commands/diff.py`
- Modify: `skills/adr-toolkit/scripts/adr.py`
- Test: `tests/unit/test_diff.py`

**Interfaces:**
- Consumes: `subprocess` (git binary on PATH).
- Produces: `run(args) -> dict` where `args` has optional `.staged` (bool), `.uncommitted` (bool), `.since` (str), `.root` (str, default `"."`). Success shape: `{"ok": True, "operation": "diff", "mode": "staged"|"uncommitted"|"since", "ref": Optional[str], "files": [{"path": str, "change_type": "added"|"modified"|"deleted", "added_lines": list, "removed_lines": list}]}`. Used by Task 6 (`check.py`).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_diff.py
import subprocess
from types import SimpleNamespace

from scripts.commands import diff


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _init_repo(tmp_path):
    _git(["init", "-q", "-b", "master"], tmp_path)
    _git(["config", "user.email", "test@example.com"], tmp_path)
    _git(["config", "user.name", "Test"], tmp_path)
    (tmp_path / "existing.py").write_text("x = 1\n", encoding="utf-8")
    _git(["add", "existing.py"], tmp_path)
    _git(["commit", "-q", "-m", "initial"], tmp_path)


def test_not_a_git_repo_returns_specific_error(tmp_path):
    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=False, uncommitted=False, since=None))
    assert result["ok"] is False
    assert result["errors"][0]["code"] == "NOT_A_GIT_REPO"


def test_uncommitted_mode_reports_added_and_removed_lines(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "existing.py").write_text("x = 1\nimport openai\n", encoding="utf-8")

    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=False, uncommitted=True, since=None))

    assert result["ok"] is True
    assert result["mode"] == "uncommitted"
    entry = next(f for f in result["files"] if f["path"] == "existing.py")
    assert entry["change_type"] == "modified"
    assert "import openai" in entry["added_lines"]


def test_staged_mode_only_sees_staged_changes(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "new_file.py").write_text("y = 2\n", encoding="utf-8")
    _git(["add", "new_file.py"], tmp_path)
    (tmp_path / "existing.py").write_text("unstaged change\n", encoding="utf-8")

    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=True, uncommitted=False, since=None))

    paths = {f["path"] for f in result["files"]}
    assert paths == {"new_file.py"}
    assert result["files"][0]["change_type"] == "added"


def test_since_ref_diffs_against_head(tmp_path):
    _init_repo(tmp_path)
    _git(["checkout", "-q", "-b", "feature"], tmp_path)
    (tmp_path / "existing.py").write_text("x = 1\nimport openai\n", encoding="utf-8")
    _git(["commit", "-q", "-am", "add import"], tmp_path)

    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=False, uncommitted=False, since="master"))

    assert result["ok"] is True
    assert result["mode"] == "since"
    assert result["ref"] == "master"
    entry = next(f for f in result["files"] if f["path"] == "existing.py")
    assert "import openai" in entry["added_lines"]


def test_invalid_ref_returns_specific_error(tmp_path):
    _init_repo(tmp_path)
    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=False, uncommitted=False, since="no-such-ref"))
    assert result["ok"] is False
    assert result["errors"][0]["code"] == "INVALID_REF"


def test_deleted_file_reports_removed_lines(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "existing.py").unlink()

    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=False, uncommitted=True, since=None))

    entry = next(f for f in result["files"] if f["path"] == "existing.py")
    assert entry["change_type"] == "deleted"
    assert "x = 1" in entry["removed_lines"]


def test_uncommitted_mode_includes_untracked_new_files(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "brand_new.py").write_text("import openai\n", encoding="utf-8")

    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=False, uncommitted=True, since=None))

    entry = next(f for f in result["files"] if f["path"] == "brand_new.py")
    assert entry["change_type"] == "added"
    assert "import openai" in entry["added_lines"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_diff.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/commands/diff.py
"""Wrap `git diff` for CHECK: staged, uncommitted, or since-a-ref changes."""
import subprocess
from pathlib import Path


def run(args) -> dict:
    root = Path(getattr(args, "root", ".")).resolve()

    repo_check = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True,
    )
    if repo_check.returncode != 0:
        return {
            "ok": False,
            "operation": "diff",
            "errors": [{"code": "NOT_A_GIT_REPO", "detail": repo_check.stderr.strip()}],
        }

    since = getattr(args, "since", None)
    if getattr(args, "staged", False):
        mode, diff_args = "staged", ["--cached"]
    elif since:
        mode, diff_args = "since", [f"{since}..HEAD"]
    else:
        mode, diff_args = "uncommitted", []

    name_status = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-status", *diff_args],
        capture_output=True, text=True,
    )
    if name_status.returncode != 0:
        code = "INVALID_REF" if since else "GIT_DIFF_FAILED"
        return {"ok": False, "operation": "diff", "errors": [{"code": code, "detail": name_status.stderr.strip()}]}

    patch = subprocess.run(
        ["git", "-C", str(root), "diff", "--unified=0", *diff_args],
        capture_output=True, text=True,
    )

    files = _parse_name_status(name_status.stdout)
    _attach_line_content(files, patch.stdout)

    if mode == "uncommitted":
        files.extend(_untracked_files(root))

    return {"ok": True, "operation": "diff", "mode": mode, "ref": since, "files": files}


def _untracked_files(root: Path) -> list:
    # `git diff` never shows untracked files, but a brand-new file is exactly
    # the kind of change CHECK needs to see (e.g. a new module that violates
    # a forbidden_import rule) — surface it as if it were entirely "added".
    listing = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True,
    )
    entries = []
    for rel_path in listing.stdout.splitlines():
        if not rel_path.strip():
            continue
        try:
            content_lines = (root / rel_path).read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            content_lines = []
        entries.append({
            "path": rel_path,
            "change_type": "added",
            "added_lines": content_lines,
            "removed_lines": [],
        })
    return entries


def _parse_name_status(output: str) -> list:
    status_map = {"A": "added", "M": "modified", "D": "deleted"}
    files = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status_char, path = parts[0][0], parts[-1]
        files.append({
            "path": path,
            "change_type": status_map.get(status_char, "modified"),
            "added_lines": [],
            "removed_lines": [],
        })
    return files


def _attach_line_content(files: list, patch_output: str) -> None:
    by_path = {f["path"]: f for f in files}
    current = None
    for line in patch_output.splitlines():
        if line.startswith("--- "):
            src = line[6:] if line.startswith("--- a/") else None
            current = by_path.get(src) if src else current
            continue
        if line.startswith("+++ "):
            dst = line[6:] if line.startswith("+++ b/") else None
            current = by_path.get(dst) if dst else current
            continue
        if current is None:
            continue
        if line.startswith("+"):
            current["added_lines"].append(line[1:])
        elif line.startswith("-"):
            current["removed_lines"].append(line[1:])
```

In `scripts/adr.py`, add:

```python
from scripts.commands import diff  # alongside other imports
```

```python
    p_diff = sub.add_parser("diff")
    p_diff.add_argument("--staged", action="store_true")
    p_diff.add_argument("--uncommitted", action="store_true")
    p_diff.add_argument("--since")
    p_diff.add_argument("--root", default=".")
    p_diff.add_argument("--json", action="store_true")
```

Add `"diff": diff.run` to `HANDLERS`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_diff.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/diff.py skills/adr-toolkit/scripts/adr.py \
        tests/unit/test_diff.py
git commit -m "feat: add diff command wrapping git diff for three range modes"
```

---

### Task 4: `rules/conflict.py` — the four constraint-matching mechanisms

**Files:**
- Create: `skills/adr-toolkit/scripts/rules/conflict.py`
- Test: `tests/unit/test_conflict.py`

**Interfaces:**
- Consumes: `scripts.core.globs.match` (Task 1).
- Produces: `evaluate_rule(rule: dict, diff_files: list, existing_paths: set) -> Optional[dict]`, `affected_paths_overlap(diff_files: list, affected_paths: list) -> bool`. `evaluate_rule` returns `None` for no violation, else `{"rule_id", "kind": "verified_violation", "severity", "message", "file", "evidence"}`. Used by Task 6 (`check.py`).

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_conflict.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/rules/conflict.py
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


def affected_paths_overlap(diff_files: list, affected_paths: list) -> bool:
    touched = _touched_paths(diff_files)
    return any(
        diff_path == ap or diff_path.startswith(ap) or globs.match(ap, diff_path)
        for diff_path in touched
        for ap in affected_paths
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_conflict.py -v`
Expected: PASS (12 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/rules/conflict.py tests/unit/test_conflict.py
git commit -m "feat: add pure constraint-matching mechanisms for CHECK"
```

---

### Task 5: `commands/check.py` — core orchestration (Accepted-ADR constraint evaluation) + CLI wiring

**Files:**
- Create: `skills/adr-toolkit/scripts/commands/check.py`
- Modify: `skills/adr-toolkit/scripts/adr.py`
- Test: `tests/unit/test_check.py`

**Interfaces:**
- Consumes: `scripts.commands.diff.run` (Task 3), `scripts.core.constraints.{extract_constraints, ConstraintsError}` (Task 2), `scripts.rules.conflict.{evaluate_rule, affected_paths_overlap}` (Task 4), `scripts.core.frontmatter.parse`/`FrontmatterError`, `scripts.core.identifiers.parse_filename`.
- Produces: `run(args) -> dict` where `args` has `.dir` (ADR directory), plus `diff`'s own `.staged`/`.uncommitted`/`.since`/`.root`. Success shape: `{"ok": True, "operation": "check", "diff": {...}, "findings": [...], "warnings": [...]}`. This task covers `Verified violation` / `Related` / `No applicable constraint` for Accepted ADRs; Task 6 extends it with `Review required` and `Superseded reference`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_check.py
import subprocess
from types import SimpleNamespace

from scripts.commands import check

RESOLUTIONS = ["fix_code", "supersede_adr", "adjust_scope", "register_exception", "false_positive"]


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _init_repo(tmp_path):
    _git(["init", "-q", "-b", "master"], tmp_path)
    _git(["config", "user.email", "test@example.com"], tmp_path)
    _git(["config", "user.name", "Test"], tmp_path)


ACCEPTED_ADR_WITH_RULE = """---
id: ADR-0001
title: Use a provider port
status: accepted
date: 2026-08-01
decision_makers: []
related: []
affected_paths:
  - src/features/
tags: []
retrospective: false
---

# Use a provider port

## Implementation Constraints

```yaml
constraints:
  - id: no-provider-sdk-in-feature
    kind: forbidden_import
    paths: ["src/features/**"]
    pattern: ["openai"]
    severity: major
    message: "Feature modules must use the LLM port."
```
"""

ACCEPTED_ADR_NO_CONSTRAINTS = """---
id: ADR-0002
title: Use flat decision directory
status: accepted
date: 2026-08-02
decision_makers: []
related: []
affected_paths:
  - docs/decisions/
tags: []
retrospective: false
---

# Use flat decision directory

No constraints block here.
"""


def _args(tmp_path, adr_dir):
    return SimpleNamespace(dir=str(adr_dir), staged=False, uncommitted=True, since=None, root=str(tmp_path))


def test_verified_violation_when_rule_fires(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-use-a-provider-port.md").write_text(ACCEPTED_ADR_WITH_RULE, encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "src" / "features").mkdir(parents=True)
    (tmp_path / "src" / "features" / "x.py").write_text("import openai\n", encoding="utf-8")

    result = check.run(_args(tmp_path, adr_dir))

    assert result["ok"] is True
    violation = next(f for f in result["findings"] if f["kind"] == "verified_violation")
    assert violation["adr_id"] == "ADR-0001"
    assert violation["rule_id"] == "no-provider-sdk-in-feature"
    assert violation["resolutions"] == RESOLUTIONS


def test_related_when_rule_present_but_does_not_fire(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-use-a-provider-port.md").write_text(ACCEPTED_ADR_WITH_RULE, encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "src" / "features").mkdir(parents=True)
    (tmp_path / "src" / "features" / "x.py").write_text("def handler(): pass\n", encoding="utf-8")

    result = check.run(_args(tmp_path, adr_dir))

    finding = next(f for f in result["findings"] if f["adr_id"] == "ADR-0001")
    assert finding["kind"] == "related"


def test_no_applicable_constraint_when_adr_has_no_constraints_block(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0002-use-flat-decision-directory.md").write_text(ACCEPTED_ADR_NO_CONSTRAINTS, encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "docs" / "decisions" / "0003-new.md").write_text("placeholder\n", encoding="utf-8")

    result = check.run(_args(tmp_path, adr_dir))

    finding = next(f for f in result["findings"] if f["adr_id"] == "ADR-0002")
    assert finding["kind"] == "no_applicable_constraint"


def test_adr_with_no_affected_path_overlap_produces_no_finding(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-use-a-provider-port.md").write_text(ACCEPTED_ADR_WITH_RULE, encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "unrelated.py").write_text("x = 1\n", encoding="utf-8")

    result = check.run(_args(tmp_path, adr_dir))

    assert result["findings"] == []


def test_malformed_adr_frontmatter_degrades_to_warning(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-use-a-provider-port.md").write_text(ACCEPTED_ADR_WITH_RULE, encoding="utf-8")
    (adr_dir / "0009-broken.md").write_text("not frontmatter at all", encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "unrelated.py").write_text("x = 1\n", encoding="utf-8")

    result = check.run(_args(tmp_path, adr_dir))

    assert result["ok"] is True
    assert any(w["code"] == "BAD_FRONTMATTER" and w["file"] == "0009-broken.md" for w in result["warnings"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_check.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/commands/check.py
"""Match a git diff against Accepted ADRs' constraints: rules and
Superseded ADRs' affected_paths, per §7/§16 of the design spec."""
from pathlib import Path

from scripts.commands import diff as diff_command
from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.constraints import ConstraintsError, extract_constraints
from scripts.rules import conflict

SKIP_FILES = {"README.md", "adr-template.md"}
RESOLUTIONS = ["fix_code", "supersede_adr", "adjust_scope", "register_exception", "false_positive"]


def run(args) -> dict:
    diff_result = diff_command.run(args)
    if not diff_result["ok"]:
        return {"ok": False, "operation": "check", "errors": diff_result["errors"]}
    diff_files = diff_result["files"]

    root = Path(getattr(args, "root", ".")).resolve()
    existing_paths = _existing_paths(root)

    adr_dir = Path(args.dir)
    entries, warnings = _load_adrs(adr_dir)

    findings = []
    for entry in entries:
        data, body = entry["data"], entry["body"]
        if data.get("status") != "accepted":
            continue
        if not conflict.affected_paths_overlap(diff_files, data.get("affected_paths", [])):
            continue

        adr_id = data.get("id")
        try:
            rules = extract_constraints(body)
        except ConstraintsError as exc:
            warnings.append({"code": "BAD_CONSTRAINTS", "adr_id": adr_id, "detail": str(exc)})
            rules = []

        produced_any = False
        for rule in rules:
            violation = conflict.evaluate_rule(rule, diff_files, existing_paths)
            if violation:
                findings.append({**violation, "adr_id": adr_id, "resolutions": RESOLUTIONS})
                produced_any = True

        if not produced_any:
            findings.append({"adr_id": adr_id, "kind": "related" if rules else "no_applicable_constraint"})

    return {
        "ok": True,
        "operation": "check",
        "diff": {"mode": diff_result["mode"], "ref": diff_result.get("ref"), "files_changed": len(diff_files)},
        "findings": findings,
        "warnings": warnings,
    }


def _load_adrs(adr_dir: Path) -> tuple:
    entries, warnings = [], []
    for entry in sorted(adr_dir.glob("*.md")):
        if entry.name in SKIP_FILES or identifiers.parse_filename(entry.name) is None:
            continue
        try:
            data, body = fm.parse(entry.read_text(encoding="utf-8"))
        except fm.FrontmatterError as exc:
            warnings.append({"code": "BAD_FRONTMATTER", "file": entry.name, "detail": str(exc)})
            continue
        entries.append({"data": data, "body": body})
    return entries, warnings


def _existing_paths(root: Path) -> set:
    paths = set()
    for entry in root.rglob("*"):
        if not entry.is_file():
            continue
        relative = entry.relative_to(root)
        if ".git" in relative.parts:
            continue
        paths.add(relative.as_posix())
    return paths
```

In `scripts/adr.py`, add:

```python
from scripts.commands import check  # alongside other imports
```

```python
    p_check = sub.add_parser("check")
    p_check.add_argument("--staged", action="store_true")
    p_check.add_argument("--uncommitted", action="store_true")
    p_check.add_argument("--since")
    p_check.add_argument("--root", default=".")
    p_check.add_argument("--dir", default="docs/decisions")
    p_check.add_argument("--json", action="store_true")
```

Add `"check": check.run` to `HANDLERS`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_check.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/check.py skills/adr-toolkit/scripts/adr.py \
        tests/unit/test_check.py
git commit -m "feat: add check command orchestrating diff against Accepted ADR constraints"
```

---

### Task 6: extend `check.py` — missing-realization heuristic + superseded-reference pass

**Files:**
- Modify: `skills/adr-toolkit/scripts/commands/check.py`
- Test: `tests/unit/test_check.py` (add cases)

**Interfaces:**
- Consumes: Task 5's `check.py` internals (`_load_adrs`, `_existing_paths`, `RESOLUTIONS`).
- Produces: two additional finding kinds on `run(args)`'s output: `review_required` (from a Verification-checklist scan, independent of whether a `constraints:` block exists) and `verified_violation` with `rule_id: "superseded_reference"` (from Superseded ADRs' `affected_paths` overlap). Both described in §16.3.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_check.py`:

```python
ACCEPTED_ADR_WITH_VERIFICATION = """---
id: ADR-0003
title: Add event replay
status: accepted
date: 2026-08-03
decision_makers: []
related: []
affected_paths:
  - src/events/
tags: []
retrospective: false
---

# Add event replay

## Verification

* `src/events/replay.py` implements the replay handler.
"""

SUPERSEDED_ADR = """---
id: ADR-0004
title: Use RabbitMQ
status: superseded
superseded_by: ADR-0005
date: 2026-07-01
decision_makers: []
related: []
affected_paths:
  - src/queue/
tags: []
retrospective: false
---

# Use RabbitMQ

Superseded.
"""


def test_review_required_when_verification_reference_is_removed(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0003-add-event-replay.md").write_text(ACCEPTED_ADR_WITH_VERIFICATION, encoding="utf-8")
    (tmp_path / "src" / "events").mkdir(parents=True)
    (tmp_path / "src" / "events" / "replay.py").write_text("def replay(): pass\n", encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "src" / "events" / "replay.py").unlink()

    result = check.run(_args(tmp_path, adr_dir))

    finding = next(f for f in result["findings"] if f["kind"] == "review_required")
    assert finding["adr_id"] == "ADR-0003"
    assert "src/events/replay.py" in finding["evidence"]["removed_paths"]


def test_superseded_reference_fires_on_affected_path_overlap(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0004-use-rabbitmq.md").write_text(SUPERSEDED_ADR, encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "src" / "queue").mkdir(parents=True)
    (tmp_path / "src" / "queue" / "client.py").write_text("x = 1\n", encoding="utf-8")

    result = check.run(_args(tmp_path, adr_dir))

    finding = next(f for f in result["findings"] if f["rule_id"] == "superseded_reference")
    assert finding["adr_id"] == "ADR-0004"
    assert finding["kind"] == "verified_violation"
    assert finding["evidence"]["superseded_by"] == "ADR-0005"
    assert finding["resolutions"] == RESOLUTIONS
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_check.py -v`
Expected: FAIL — the two new finding kinds aren't produced yet.

- [ ] **Step 3: Extend the implementation**

In `skills/adr-toolkit/scripts/commands/check.py`, add near the top:

```python
import re

VERIFICATION_HEADING_RE = re.compile(r"^#+\s*Verification\s*$", re.IGNORECASE | re.MULTILINE)
NEXT_HEADING_RE = re.compile(r"^#+\s", re.MULTILINE)
PATH_TOKEN_RE = re.compile(r"`([^`]+\.[a-zA-Z0-9]+)`")
```

Replace the Accepted-ADR loop body's `if not produced_any:` block with (keeping everything above it unchanged):

```python
        review = _missing_realization(body, diff_files)
        if review:
            findings.append({"adr_id": adr_id, "kind": "review_required", **review})
            produced_any = True

        if not produced_any:
            findings.append({"adr_id": adr_id, "kind": "related" if rules else "no_applicable_constraint"})
```

After the Accepted-ADR loop, before the `return`, add the Superseded-ADR pass:

```python
    for entry in entries:
        data = entry["data"]
        if data.get("status") != "superseded":
            continue
        if not conflict.affected_paths_overlap(diff_files, data.get("affected_paths", [])):
            continue
        findings.append({
            "adr_id": data.get("id"),
            "kind": "verified_violation",
            "rule_id": "superseded_reference",
            "severity": "major",
            "message": (
                f"This path is governed by {data.get('id')}, which is superseded "
                f"by {data.get('superseded_by')}. Review the replacement decision "
                f"before proceeding."
            ),
            "file": None,
            "evidence": {"superseded_by": data.get("superseded_by")},
            "resolutions": RESOLUTIONS,
        })
```

Add the missing-realization heuristic function:

```python
def _missing_realization(body: str, diff_files: list):
    heading = VERIFICATION_HEADING_RE.search(body)
    if not heading:
        return None
    next_heading = NEXT_HEADING_RE.search(body, heading.end())
    section = body[heading.end():next_heading.start() if next_heading else len(body)]

    referenced_paths = PATH_TOKEN_RE.findall(section)
    if not referenced_paths:
        return None

    by_path = {f["path"]: f for f in diff_files}
    removed = [p for p in referenced_paths if by_path.get(p, {}).get("change_type") == "deleted"]
    if not removed:
        return None

    return {
        "message": f"Verification references {removed} which this diff removes.",
        "evidence": {"removed_paths": removed},
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_check.py -v`
Expected: PASS (7 tests — the 5 from Task 5 plus these 2)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/check.py tests/unit/test_check.py
git commit -m "feat: add missing-realization and superseded-reference findings to check"
```

---

### Task 7: `references/conflict-rules.md` — constraint-authoring reference

**Files:**
- Create: `skills/adr-toolkit/references/conflict-rules.md`
- Test: `tests/unit/test_conflict_rules_reference.py`

**Interfaces:**
- Consumes: nothing (content only, read by the agent when drafting or explaining `constraints:` blocks and when presenting CHECK findings).
- Produces: the human/agent-readable explanation of the six rule kinds, the four-way classification, and the five resolution options.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_conflict_rules_reference.py
from pathlib import Path

REFERENCE = (
    Path(__file__).resolve().parent.parent.parent
    / "skills" / "adr-toolkit" / "references" / "conflict-rules.md"
)


def test_reference_documents_all_six_rule_kinds():
    text = REFERENCE.read_text(encoding="utf-8")
    for kind in [
        "forbidden_import", "required_path", "forbidden_path",
        "dependency_forbidden", "file_must_exist", "test_must_exist",
    ]:
        assert kind in text


def test_reference_documents_the_four_classifications():
    text = REFERENCE.read_text(encoding="utf-8")
    for label in ["Related", "Review required", "Verified violation", "No applicable constraint"]:
        assert label in text


def test_reference_documents_the_five_resolutions():
    text = REFERENCE.read_text(encoding="utf-8")
    for resolution in ["fix_code", "supersede_adr", "adjust_scope", "register_exception", "false_positive"]:
        assert resolution in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_conflict_rules_reference.py -v`
Expected: FAIL — file doesn't exist.

- [ ] **Step 3: Write the content**

```markdown
<!-- skills/adr-toolkit/references/conflict-rules.md -->
# Conflict Rules Reference

CHECK matches a diff against Accepted ADRs' `constraints:` blocks and
Superseded ADRs' `affected_paths` — structural evidence only, never
semantic/AST analysis (see the design spec §7).

## Writing a `constraints:` block

Add a fenced YAML block to an ADR's `Implementation Constraints` section:

```yaml
constraints:
  - id: no-provider-sdk-in-feature
    kind: forbidden_import
    paths: ["src/features/**"]
    pattern: ["openai\\.", "anthropic\\."]
    severity: major
    message: "Feature modules must use the LLM port."
```

Each rule needs `id`, `kind`, `paths` (glob list, `**` matches any depth),
`severity`, and `message`; `pattern` is required by every kind except the
existence-check kinds. `paths`/`pattern` values must be a JSON-style array
on one line — not YAML block-list syntax.

## The six rule kinds

- `forbidden_import` — fires if an added line in a file matching `paths`
  matches any regex in `pattern`. Use for "this module must never import X."
- `dependency_forbidden` — mechanically identical to `forbidden_import`;
  scope `paths` to a dependency manifest (`requirements.txt`,
  `package.json`) instead of source files.
- `required_path` — fires if the diff touches a file matching `paths` but
  no file matching `pattern` is touched by the diff or already exists in
  the repository. Use for "touching X requires also touching/having Y."
- `forbidden_path` — fires if the diff touches a file matching `paths` AND
  also touches a file matching `pattern`. Use for boundary violations
  ("features must never touch db migrations directly").
- `file_must_exist` / `test_must_exist` — fires if none of the paths
  matching `paths` exist in the working tree after the diff. Identical
  mechanism; `test_must_exist` is a naming convention for the ADR author,
  not different logic.

An ADR with no `constraints:` block has nothing CHECK can mechanically
enforce — that's a legitimate state, not an error.

## Four-way classification

- **Related** — the diff touches a path the ADR names, and its
  `constraints:` block was evaluated but nothing fired.
- **Review required** — the ADR's `Verification` checklist references a
  path or test the diff removes; this is prose-scanning, not a
  `constraints:` rule, so it needs a human look rather than a mechanical
  yes/no.
- **Verified violation** — a `constraints:` rule fired with direct
  structural evidence, or the diff touches a path a Superseded ADR
  governs (`rule_id: superseded_reference`).
- **No applicable constraint** — the diff touches a path the ADR names,
  but the ADR has neither a `constraints:` block nor a matching
  Verification reference.

## Resolving a Verified violation

Present all five options; never default to "revert the code":

1. `fix_code` — change the diff to comply with the existing decision.
2. `supersede_adr` — the old decision no longer holds; record a new ADR
   that supersedes it (`adr.py supersede`).
3. `adjust_scope` — the ADR's `affected_paths` or `constraints:` are too
   broad or too narrow; edit them instead of the code.
4. `register_exception` — this specific case is a deliberate, documented
   exception to an otherwise-still-valid rule.
5. `false_positive` — the rule fired but there is no real conflict; note
   why so the rule can be tightened.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_conflict_rules_reference.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/references/conflict-rules.md tests/unit/test_conflict_rules_reference.py
git commit -m "docs: add conflict rules reference for CHECK"
```

---

### Task 8: `SKILL.md` — CHECK section

**Files:**
- Modify: `skills/adr-toolkit/SKILL.md`
- Test: `tests/unit/test_skill_manifest.py` (add cases)

**Interfaces:**
- Consumes: `diff`/`check` (Tasks 3, 5, 6), `references/conflict-rules.md` (Task 7).
- Produces: the CHECK operation contract an agent follows, replacing the "CHECK is not yet implemented" note in `## Script reference`.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_skill_manifest.py`:

```python
def test_skill_md_documents_check():
    _, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    assert "## CHECK" in body
    assert "adr.py check" in body
    assert "Verified violation" in body
    assert "CHECK is not yet implemented" not in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_skill_manifest.py -v`
Expected: FAIL — section doesn't exist yet, and the stale note is still present.

- [ ] **Step 3: Add the section**

Insert into `skills/adr-toolkit/SKILL.md`, after `## Lifecycle operations` and before `## Prohibited`:

```markdown
## CHECK

Use CHECK to look for structural conflicts between a diff and existing
Accepted/Superseded ADRs before or during a change — never after merging,
since CHECK is read-only and never fixes anything itself.

1. **PREFLIGHT** — run
   `python skills/adr-toolkit/scripts/adr.py preflight --json`. If
   `existing_adr_directory` is `null`, stop and tell the user to run INIT
   first.
2. **GATHER EVIDENCE** — run
   `python skills/adr-toolkit/scripts/adr.py check --uncommitted --dir docs/decisions --json`
   (or `--staged`, or `--since <ref>` for a branch/commit range — pick the
   mode that matches what the user asked to check). Read
   `references/conflict-rules.md` if you need to explain a finding or help
   the user write a `constraints:` block.
3. **CLASSIFY** — each finding already carries its classification
   (`related`, `review_required`, `verified_violation`,
   `no_applicable_constraint`); do not re-judge it, report it as returned.
4. **REPORT** — group findings by classification. For every
   `verified_violation`, present all five resolutions from
   `references/conflict-rules.md` (`fix_code`, `supersede_adr`,
   `adjust_scope`, `register_exception`, `false_positive`) — never assume
   which one the user wants.
5. **ASK-IF-NEEDED / MUTATE** — CHECK itself never writes anything. If the
   user picks `fix_code`, that's a normal code edit, not an ADR Toolkit
   operation. If they pick `supersede_adr` or `adjust_scope`, follow the
   RECORD or Lifecycle operations flow above — never hand-edit
   `constraints:`, `affected_paths`, or `status`.
6. Any `check` `warnings` entries (e.g. `BAD_FRONTMATTER`,
   `BAD_CONSTRAINTS`) mean one ADR was skipped, not that CHECK failed —
   report them, but don't block on them.
```

Also, in `## Script reference`, replace:

```markdown
CHECK is not yet implemented (see `project-roadmap.md` in the repository root
and the design spec this skill is built from).
```

with:

```markdown
CHECK's conflict detection is deliberately limited to structural evidence
from `constraints:` blocks (see `references/conflict-rules.md`) — it never
attempts semantic or AST-level analysis; see `project-roadmap.md` for what
that fuller scope would look like.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_skill_manifest.py -v`
Expected: PASS (all prior cases plus this one)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/SKILL.md tests/unit/test_skill_manifest.py
git commit -m "feat: document CHECK operation in SKILL.md"
```

---

### Task 9: End-to-end RECORD-then-CHECK fixture and golden test

**Files:**
- Create: `tests/fixtures/check_provider_port/docs/decisions/0001-use-a-provider-port.md`
- Create: `tests/integration/test_check_workflow.py`

**Interfaces:**
- Consumes: `check`, `diff` via subprocess (Tasks 3, 5, 6), following the `_run` diagnostic-assertion pattern established in `tests/integration/test_record_workflow.py`.
- Produces: the golden proof that CHECK's scripted steps compose correctly against a repo with a real git history and a constraint-bearing Accepted ADR.

- [ ] **Step 1: Write the failing test**

```markdown
<!-- tests/fixtures/check_provider_port/docs/decisions/0001-use-a-provider-port.md -->
---
id: ADR-0001
title: Use a provider port for LLM calls
status: accepted
date: 2026-08-01
decision_makers: []
related: []
affected_paths:
  - src/features/
tags:
  - architecture
retrospective: false
---

# Use a provider port for LLM calls

## Implementation Constraints

Feature modules must go through the LLM port; they must never import a
provider SDK directly.

```yaml
constraints:
  - id: no-provider-sdk-in-feature
    kind: forbidden_import
    paths: ["src/features/**"]
    pattern: ["openai", "anthropic"]
    severity: major
    message: "Feature modules must use the LLM port, not a provider SDK directly."
```
```

```python
# tests/integration/test_check_workflow.py
import json
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "check_provider_port"
ADR_PY = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit" / "scripts" / "adr.py"


def _run(args, cwd):
    command = [sys.executable, str(ADR_PY), *args]
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    assert result.returncode == 0, (
        f"CLI command failed: {' '.join(command)}\n"
        f"cwd: {cwd}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"CLI command did not return JSON: {' '.join(command)}\n"
            f"cwd: {cwd}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        ) from exc
    assert payload.get("ok") is True, (
        f"CLI command reported failure: {' '.join(command)}\ncwd: {cwd}\npayload: {payload!r}"
    )
    return payload


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_check_flags_a_violation_then_clears_after_the_fix(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)
    _git(["init", "-q", "-b", "master"], repo)
    _git(["config", "user.email", "test@example.com"], repo)
    _git(["config", "user.name", "Test"], repo)
    _git(["add", "-A"], repo)
    _git(["commit", "-q", "-m", "init"], repo)

    features_dir = repo / "src" / "features"
    features_dir.mkdir(parents=True)
    (features_dir / "chat.py").write_text("import openai\n\ndef handler():\n    pass\n", encoding="utf-8")

    violating_result = _run(
        ["check", "--uncommitted", "--dir", "docs/decisions", "--json"], cwd=repo,
    )
    violation = next(f for f in violating_result["findings"] if f["kind"] == "verified_violation")
    assert violation["adr_id"] == "ADR-0001"
    assert violation["rule_id"] == "no-provider-sdk-in-feature"
    assert set(violation["resolutions"]) == {
        "fix_code", "supersede_adr", "adjust_scope", "register_exception", "false_positive",
    }

    (features_dir / "chat.py").write_text(
        "from src.core.ports.llm import LLMPort\n\ndef handler():\n    pass\n", encoding="utf-8",
    )

    fixed_result = _run(
        ["check", "--uncommitted", "--dir", "docs/decisions", "--json"], cwd=repo,
    )
    assert all(f["kind"] != "verified_violation" for f in fixed_result["findings"])
    related = next(f for f in fixed_result["findings"] if f["adr_id"] == "ADR-0001")
    assert related["kind"] == "related"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/integration/test_check_workflow.py -v`
Expected: FAIL until Step 1's fixture file exists.

- [ ] **Step 3: Nothing further to implement**

This task's "implementation" is the fixture itself. No production code changes — it proves Tasks 1–8 already compose correctly end to end, including that fixing the violation clears it on a second `check` run.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/integration/test_check_workflow.py -v`
Expected: PASS (1 test)

Then run the full suite:

Run: `python -m pytest tests/unit tests/integration -v`
Expected: PASS (all prior tests plus this plan's new ones)

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/check_provider_port tests/integration/test_check_workflow.py
git commit -m "test: add end-to-end CHECK fixture and golden test"
```

---

## Plan self-review notes

- **Spec coverage:** §7 (six rule kinds, four-way classification, five resolutions) → Tasks 2, 4, 5, 6, 7. §11 CHECK data flow → Tasks 3, 5, 6, 8. §16.1 module split → Tasks 1–6 (`globs.py`/`constraints.py` under `core/`, `conflict.py` under `rules/`, `diff.py`/`check.py` under `commands/`). §16.2 matching mechanisms → Task 4. §16.3 classification algorithm → Tasks 5–6. §16.4 constraints scope (Accepted only) → Task 5's `if data.get("status") != "accepted": continue`. §16.5 diff CLI shape → Task 3. §16.6 output/error handling → Tasks 3, 5 (specific error codes; `warnings` degrade path). §16.7 testing strategy → every task's own unit tests plus Task 9's golden test.
- **Type consistency checked:** `diff.run`'s `files` shape (`{path, change_type, added_lines, removed_lines}`, Task 3) matches exactly what `conflict.py` (Task 4) and `check.py` (Tasks 5–6) consume. `conflict.evaluate_rule`'s return shape (`rule_id`/`kind`/`severity`/`message`/`file`/`evidence`) matches how Task 5 merges it into a finding (`{**violation, "adr_id", "resolutions"}`). `extract_constraints`'s rule dicts (Task 2: `id`/`kind`/`paths`/`pattern`/`severity`/`message`) match the field names `conflict.py` reads. `RESOLUTIONS` is defined once in `check.py` and reused for both `constraints:`-sourced and `superseded_reference` violations, not duplicated.
- **No placeholders found.**
