# ADR Toolkit — Core Scripts + INIT (Plan 1 of 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a self-contained `skills/adr-toolkit/` package with the deterministic script layer (frontmatter, IDs, lifecycle, schema, discovery, index, validation) and two fully working operations — INIT (scaffolding) and DISCOVER (past-decision recovery, kept separate from INIT per user feedback) — usable three ways: through Claude Code, through any other harness via a generic fallback adapter, or directly from the terminal with no AI agent at all via an interactive CLI wizard. CI enforces all of it from the first commit.

**Architecture:** Deterministic Python stdlib-only scripts under `skills/adr-toolkit/scripts/` (package name `scripts`, imported as `scripts.core.*` / `scripts.commands.*` / `scripts.evidence.*`) do all file I/O, ID assignment, and validation. `SKILL.md` carries the workflow contract the agent follows and never re-implements those deterministic steps in prose. A thin Claude Code adapter under `adapters/claude/` points at the skill folder; it carries no logic of its own.

**Tech Stack:** Python 3.9+ standard library only (argparse, pathlib, json, re, shutil, datetime). pytest for tests. GitHub Actions for CI.

**Spec:** `docs/superpowers/specs/2026-08-29-adr-toolkit-design.md`

## Global Constraints

- Python 3.9+, standard library only — no third-party pip packages anywhere under `skills/adr-toolkit/`.
- UTF-8 explicit on every file read/write: always pass `encoding="utf-8"`.
- No `shell=True` and no string-interpolated subprocess commands — pass argument lists.
- `init` and `create` (the two mutating commands in this plan) must support `--dry-run` and must refuse to overwrite an existing file or non-empty directory instead of silently overwriting it.
- Command modules never `print()` — they return a `dict`; only `scripts/adr.py`'s `main()` serializes to stdout as JSON.
- ADR IDs are 4-digit zero-padded, computed as `max(existing IDs) + 1` from filenames already on disk — never guessed, never reused.
- **Out of scope for this plan** (tracked in `project-roadmap.md` / later plans): RECORD workflow, CHECK workflow, i18n wiring, Codex/Gemini CLI/Antigravity adapters, release automation. `index.py`'s section headers are English-only in this plan; localizing them is Plan 4's job.
- Every task must leave `python -m pytest tests/unit tests/integration -v` green (from the repo root) before its commit step.
- Avoid `X | None` union-type syntax (Python 3.10+); use `typing.Optional` so the code runs on the Python 3.9 floor declared by `preflight`.

---

### Task 1: Scaffold the self-contained skill package and test plumbing

**Files:**
- Create: `skills/adr-toolkit/VERSION`
- Create: `skills/adr-toolkit/scripts/__init__.py`
- Create: `skills/adr-toolkit/scripts/core/__init__.py`
- Create: `skills/adr-toolkit/scripts/commands/__init__.py`
- Create: `skills/adr-toolkit/scripts/evidence/__init__.py`
- Create: `skills/adr-toolkit/templates/.gitkeep`
- Create: `skills/adr-toolkit/references/.gitkeep`
- Create: `skills/adr-toolkit/schemas/.gitkeep`
- Create: `tests/conftest.py`
- Create: `pytest.ini`
- Test: `tests/unit/test_scaffold.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: `sys.path` entry for `skills/adr-toolkit/` set up by `tests/conftest.py`, so every later test file can `import scripts.core.xxx` / `import scripts.commands.xxx` / `import scripts.evidence.xxx` without its own path hacking.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_scaffold.py
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit"


def test_skill_root_layout_exists():
    assert (SKILL_ROOT / "VERSION").is_file()
    assert (SKILL_ROOT / "scripts" / "__init__.py").is_file()
    assert (SKILL_ROOT / "scripts" / "core" / "__init__.py").is_file()
    assert (SKILL_ROOT / "scripts" / "commands" / "__init__.py").is_file()
    assert (SKILL_ROOT / "scripts" / "evidence" / "__init__.py").is_file()
    assert (SKILL_ROOT / "templates").is_dir()
    assert (SKILL_ROOT / "references").is_dir()
    assert (SKILL_ROOT / "schemas").is_dir()


def test_version_file_has_semver():
    version = (SKILL_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    parts = version.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_scripts_importable_via_conftest_path():
    import scripts  # noqa: F401 — only importable if conftest.py set sys.path correctly
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_scaffold.py -v`
Expected: FAIL / ERROR — files and directories don't exist yet, `tests/conftest.py` doesn't exist.

- [ ] **Step 3: Create the scaffold**

```python
# tests/conftest.py
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent / "skills" / "adr-toolkit"
sys.path.insert(0, str(SKILL_ROOT))
```

```ini
# pytest.ini
[pytest]
testpaths = tests
```

Create the directories and empty `__init__.py` files listed under **Files** above (empty file contents), a `.gitkeep` in each of `templates/`, `references/`, `schemas/` (filled by later tasks), and:

```text
skills/adr-toolkit/VERSION
0.1.0
```

(no trailing content beyond the version string and a newline)

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_scaffold.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/VERSION skills/adr-toolkit/scripts skills/adr-toolkit/templates \
        skills/adr-toolkit/references skills/adr-toolkit/schemas tests/conftest.py pytest.ini \
        tests/unit/test_scaffold.py
git commit -m "feat: scaffold self-contained adr-toolkit skill package"
```

---

### Task 2: `core/frontmatter.py` — parse and serialize ADR YAML frontmatter

**Files:**
- Create: `skills/adr-toolkit/scripts/core/frontmatter.py`
- Test: `tests/unit/test_frontmatter.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `parse(text: str) -> tuple[dict, str]`, `serialize(data: dict, body: str) -> str`, `FrontmatterError(ValueError)`. Used by Tasks 10 (create), 11 (index), 12 (validate).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_frontmatter.py
import pytest

from scripts.core import frontmatter as fm


def test_parse_extracts_scalars_lists_and_body():
    text = (
        "---\n"
        "id: ADR-0003\n"
        "title: Use a provider port\n"
        "status: accepted\n"
        "date: 2026-08-29\n"
        "decision_makers:\n"
        "  - Yangseunghyeon\n"
        "related: []\n"
        "affected_paths:\n"
        "  - src/providers/\n"
        "  - src/core/ports/\n"
        "tags:\n"
        "  - architecture\n"
        "retrospective: false\n"
        "---\n"
        "\n"
        "# Use a provider port\n"
        "\n"
        "Body content.\n"
    )
    data, body = fm.parse(text)

    assert data["id"] == "ADR-0003"
    assert data["decision_makers"] == ["Yangseunghyeon"]
    assert data["affected_paths"] == ["src/providers/", "src/core/ports/"]
    assert data["retrospective"] is False
    assert body.strip().startswith("# Use a provider port")


def test_parse_raises_without_frontmatter_block():
    with pytest.raises(fm.FrontmatterError):
        fm.parse("# No frontmatter here\n")


def test_serialize_round_trips_through_parse():
    data = {
        "id": "ADR-0001",
        "title": "Record architecture decisions",
        "status": "accepted",
        "date": "2026-08-29",
        "decision_makers": [],
        "related": [],
        "affected_paths": ["docs/decisions/"],
        "tags": ["process"],
        "retrospective": False,
    }
    text = fm.serialize(data, "# Record architecture decisions\n\nBody.\n")
    parsed_data, parsed_body = fm.parse(text)

    assert parsed_data == data
    assert parsed_body.strip() == "# Record architecture decisions\n\nBody."
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_frontmatter.py -v`
Expected: FAIL — `scripts.core.frontmatter` doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/core/frontmatter.py
"""Parse and serialize ADR YAML frontmatter without a YAML library dependency.

Supports exactly the subset ADR Toolkit frontmatter needs: string scalars,
booleans, and flat string lists. Not a general YAML parser.
"""
import re

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.DOTALL)


class FrontmatterError(ValueError):
    pass


def parse(text: str) -> tuple:
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise FrontmatterError("No YAML frontmatter block found")
    raw_yaml, body = match.group(1), match.group(2)
    return _parse_simple_yaml(raw_yaml), body


def serialize(data: dict, body: str) -> str:
    lines = ["---"]
    for key, value in data.items():
        lines.append(_format_field(key, value))
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body


def _parse_simple_yaml(raw: str) -> dict:
    data: dict = {}
    current_list_key = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.startswith("  - "):
            if current_list_key is None:
                raise FrontmatterError(f"List item with no preceding key: {line!r}")
            data[current_list_key].append(line.strip()[2:].strip())
            continue
        if ":" not in line:
            raise FrontmatterError(f"Malformed frontmatter line: {line!r}")
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "" or value == "[]":
            data[key] = []
            current_list_key = key if value == "" else None
        else:
            current_list_key = None
            if value.lower() in ("true", "false"):
                data[key] = value.lower() == "true"
            else:
                data[key] = value.strip('"').strip("'")
    return data


def _format_field(key: str, value) -> str:
    if isinstance(value, list):
        if not value:
            return f"{key}: []"
        item_lines = "\n".join(f"  - {item}" for item in value)
        return f"{key}:\n{item_lines}"
    if isinstance(value, bool):
        return f"{key}: {'true' if value else 'false'}"
    return f"{key}: {value}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_frontmatter.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/core/frontmatter.py tests/unit/test_frontmatter.py
git commit -m "feat: add hand-rolled frontmatter parser/serializer"
```

---

### Task 3: `core/identifiers.py` — ADR ID calculation, filenames, slugs

**Files:**
- Create: `skills/adr-toolkit/scripts/core/identifiers.py`
- Test: `tests/unit/test_identifiers.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `parse_filename(filename: str) -> Optional[tuple]`, `next_id(adr_dir: Path) -> int`, `format_filename(adr_id: int, slug: str) -> str`, `slugify(title: str) -> str`. Used by Tasks 10 (create), 11 (index), 12 (validate).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_identifiers.py
from pathlib import Path

from scripts.core import identifiers


def test_parse_filename_extracts_id_and_slug():
    assert identifiers.parse_filename("0003-use-provider-port.md") == (3, "use-provider-port")


def test_parse_filename_rejects_non_matching_names():
    assert identifiers.parse_filename("README.md") is None
    assert identifiers.parse_filename("3-too-short.md") is None


def test_next_id_is_one_past_the_highest_existing(tmp_path):
    (tmp_path / "0001-a.md").write_text("x", encoding="utf-8")
    (tmp_path / "0003-b.md").write_text("x", encoding="utf-8")
    assert identifiers.next_id(tmp_path) == 4


def test_next_id_starts_at_one_for_empty_directory(tmp_path):
    assert identifiers.next_id(tmp_path) == 1


def test_format_filename_zero_pads_to_four_digits():
    assert identifiers.format_filename(7, "use-kafka") == "0007-use-kafka.md"


def test_slugify_lowercases_and_hyphenates():
    assert identifiers.slugify("Use Kafka for Domain Events!") == "use-kafka-for-domain-events"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_identifiers.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/core/identifiers.py
"""ADR ID calculation, filename parsing, and title slugification."""
import re
from pathlib import Path
from typing import Optional

ADR_FILENAME_RE = re.compile(r"^(\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")


def parse_filename(filename: str) -> Optional[tuple]:
    match = ADR_FILENAME_RE.match(filename)
    if not match:
        return None
    return int(match.group(1)), match.group(2)


def next_id(adr_dir: Path) -> int:
    existing_ids = []
    for entry in adr_dir.glob("*.md"):
        parsed = parse_filename(entry.name)
        if parsed:
            existing_ids.append(parsed[0])
    return max(existing_ids, default=0) + 1


def format_filename(adr_id: int, slug: str) -> str:
    return f"{adr_id:04d}-{slug}.md"


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return re.sub(r"-+", "-", slug)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_identifiers.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/core/identifiers.py tests/unit/test_identifiers.py
git commit -m "feat: add ADR id/filename/slug calculation"
```

---

### Task 4: `core/lifecycle.py` — status transition rules

**Files:**
- Create: `skills/adr-toolkit/scripts/core/lifecycle.py`
- Test: `tests/unit/test_lifecycle.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `STATUSES: set`, `validate_transition(current: str, target: str) -> None`, `InvalidTransitionError(ValueError)`. `STATUSES` is consumed by Task 5 (`core/schema.py`).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_lifecycle.py
import pytest

from scripts.core import lifecycle


def test_proposed_can_become_accepted():
    lifecycle.validate_transition("proposed", "accepted")  # must not raise


def test_proposed_can_become_rejected():
    lifecycle.validate_transition("proposed", "rejected")  # must not raise


def test_accepted_cannot_go_back_to_proposed():
    with pytest.raises(lifecycle.InvalidTransitionError):
        lifecycle.validate_transition("accepted", "proposed")


def test_rejected_is_terminal():
    with pytest.raises(lifecycle.InvalidTransitionError):
        lifecycle.validate_transition("rejected", "accepted")


def test_unknown_status_is_rejected():
    with pytest.raises(lifecycle.InvalidTransitionError):
        lifecycle.validate_transition("accepted", "archived")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_lifecycle.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/core/lifecycle.py
"""ADR status lifecycle rules."""

STATUSES = {"proposed", "accepted", "rejected", "deprecated", "superseded"}

ALLOWED_TRANSITIONS = {
    "proposed": {"accepted", "rejected"},
    "accepted": {"deprecated", "superseded"},
    "rejected": set(),
    "deprecated": set(),
    "superseded": set(),
}


class InvalidTransitionError(ValueError):
    pass


def validate_transition(current: str, target: str) -> None:
    if current not in STATUSES:
        raise InvalidTransitionError(f"Unknown current status: {current!r}")
    if target not in STATUSES:
        raise InvalidTransitionError(f"Unknown target status: {target!r}")
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransitionError(f"Cannot transition from {current!r} to {target!r}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_lifecycle.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/core/lifecycle.py tests/unit/test_lifecycle.py
git commit -m "feat: add ADR lifecycle transition rules"
```

---

### Task 5: `core/schema.py` — frontmatter structural validation

**Files:**
- Create: `skills/adr-toolkit/scripts/core/schema.py`
- Create: `skills/adr-toolkit/schemas/adr.schema.json` (human/tool-readable reference; `core/schema.py` is the enforced source of truth, kept in sync by hand)
- Test: `tests/unit/test_schema.py`

**Interfaces:**
- Consumes: `scripts.core.lifecycle.STATUSES` (Task 4).
- Produces: `validate_frontmatter(data: dict) -> list`. Used by Tasks 10 (create) and 12 (validate).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_schema.py
from scripts.core.schema import validate_frontmatter

VALID = {
    "id": "ADR-0001",
    "title": "Record architecture decisions",
    "status": "accepted",
    "date": "2026-08-29",
    "decision_makers": [],
    "related": [],
    "affected_paths": ["docs/decisions/"],
    "tags": ["process"],
    "retrospective": False,
}


def test_valid_frontmatter_has_no_errors():
    assert validate_frontmatter(VALID) == []


def test_missing_field_is_reported():
    data = dict(VALID)
    del data["status"]
    errors = validate_frontmatter(data)
    assert any("status" in e for e in errors)


def test_bad_id_format_is_reported():
    data = dict(VALID, id="0001")
    errors = validate_frontmatter(data)
    assert any("id" in e for e in errors)


def test_unknown_status_is_reported():
    data = dict(VALID, status="archived")
    errors = validate_frontmatter(data)
    assert any("status" in e for e in errors)


def test_bad_date_format_is_reported():
    data = dict(VALID, date="29-08-2026")
    errors = validate_frontmatter(data)
    assert any("date" in e for e in errors)


def test_wrong_type_is_reported():
    data = dict(VALID, tags="process")  # should be a list
    errors = validate_frontmatter(data)
    assert any("tags" in e for e in errors)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_schema.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/core/schema.py
"""Structural validation for ADR frontmatter.

schemas/adr.schema.json documents the same shape for external tools; this
module is the version actually enforced at runtime.
"""
from datetime import date as date_cls

from scripts.core.lifecycle import STATUSES

REQUIRED_FIELDS = {
    "id": str,
    "title": str,
    "status": str,
    "date": str,
    "decision_makers": list,
    "related": list,
    "affected_paths": list,
    "tags": list,
    "retrospective": bool,
}

import re

ID_RE = re.compile(r"^ADR-\d{4}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_frontmatter(data: dict) -> list:
    errors = []
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in data:
            errors.append(f"missing required field: {field}")
            continue
        if not isinstance(data[field], expected_type):
            errors.append(
                f"field {field!r} must be {expected_type.__name__}, "
                f"got {type(data[field]).__name__}"
            )

    if isinstance(data.get("id"), str) and not ID_RE.match(data["id"]):
        errors.append(f"id {data['id']!r} does not match ADR-NNNN")

    if "status" in data and data["status"] not in STATUSES:
        errors.append(f"status {data['status']!r} is not one of {sorted(STATUSES)}")

    if isinstance(data.get("date"), str):
        if not DATE_RE.match(data["date"]):
            errors.append(f"date {data['date']!r} is not YYYY-MM-DD")
        else:
            year, month, day = (int(part) for part in data["date"].split("-"))
            try:
                date_cls(year, month, day)
            except ValueError:
                errors.append(f"date {data['date']!r} is not a real calendar date")

    return errors
```

```json
// skills/adr-toolkit/schemas/adr.schema.json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ADR Frontmatter",
  "type": "object",
  "required": ["id", "title", "status", "date", "decision_makers", "related", "affected_paths", "tags", "retrospective"],
  "properties": {
    "id": { "type": "string", "pattern": "^ADR-[0-9]{4}$" },
    "title": { "type": "string" },
    "status": { "type": "string", "enum": ["proposed", "accepted", "rejected", "deprecated", "superseded"] },
    "date": { "type": "string", "format": "date" },
    "decision_makers": { "type": "array", "items": { "type": "string" } },
    "related": { "type": "array", "items": { "type": "string" } },
    "affected_paths": { "type": "array", "items": { "type": "string" } },
    "tags": { "type": "array", "items": { "type": "string" } },
    "retrospective": { "type": "boolean" }
  }
}
```

Delete `skills/adr-toolkit/schemas/.gitkeep` now that the directory has a real file.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_schema.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git rm skills/adr-toolkit/schemas/.gitkeep
git add skills/adr-toolkit/scripts/core/schema.py skills/adr-toolkit/schemas/adr.schema.json \
        tests/unit/test_schema.py
git commit -m "feat: add ADR frontmatter schema validation"
```

---

### Task 6: `commands/preflight.py` — environment and existing-convention check

**Files:**
- Create: `skills/adr-toolkit/scripts/commands/preflight.py`
- Test: `tests/unit/test_preflight.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `run(args) -> dict` where `args` has an optional `.root` attribute (defaults to `"."`). Return shape: `{"ok": bool, "operation": "preflight", "python_version": str, "git_available": bool, "existing_adr_directory": Optional[str], "warnings": list, "errors": list}`. Used by Task 14 (CLI entrypoint) and Task 17 (fixture test).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_preflight.py
from types import SimpleNamespace

from scripts.commands import preflight


def test_reports_no_existing_adr_directory(tmp_path):
    result = preflight.run(SimpleNamespace(root=str(tmp_path)))
    assert result["ok"] is True
    assert result["existing_adr_directory"] is None


def test_detects_existing_docs_decisions_directory(tmp_path):
    (tmp_path / "docs" / "decisions").mkdir(parents=True)
    result = preflight.run(SimpleNamespace(root=str(tmp_path)))
    assert result["existing_adr_directory"] == "docs/decisions"


def test_reports_git_availability(tmp_path):
    result = preflight.run(SimpleNamespace(root=str(tmp_path)))
    assert isinstance(result["git_available"], bool)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_preflight.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/commands/preflight.py
"""Check that the environment has what ADR Toolkit needs to run."""
import shutil
import sys
from pathlib import Path

CANDIDATE_ADR_DIRS = ("docs/decisions", "docs/adr", "adr", "decisions")


def run(args) -> dict:
    errors = []

    if sys.version_info < (3, 9):
        errors.append({"code": "PYTHON_TOO_OLD", "detail": sys.version})

    git_path = shutil.which("git")

    root = Path(getattr(args, "root", ".")).resolve()
    existing_dir = None
    for candidate in CANDIDATE_ADR_DIRS:
        if (root / candidate).is_dir():
            existing_dir = candidate
            break

    warnings = []
    if git_path is None:
        warnings.append({"code": "GIT_NOT_FOUND"})

    return {
        "ok": not errors,
        "operation": "preflight",
        "python_version": sys.version.split()[0],
        "git_available": git_path is not None,
        "existing_adr_directory": existing_dir,
        "warnings": warnings,
        "errors": errors,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_preflight.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/preflight.py tests/unit/test_preflight.py
git commit -m "feat: add preflight environment check"
```

---

### Task 7: `evidence/dependency_scanner.py` — dependency manifest detection

**Files:**
- Create: `skills/adr-toolkit/scripts/evidence/dependency_scanner.py`
- Test: `tests/unit/test_dependency_scanner.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `scan(root: Path) -> list` where each item is `{"ecosystem": str, "path": str}`. Used by Task 8 (`commands/discover.py`).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_dependency_scanner.py
from pathlib import Path

from scripts.evidence import dependency_scanner


def test_detects_npm_manifest(tmp_path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    findings = dependency_scanner.scan(tmp_path)
    assert {"ecosystem": "npm", "path": "package.json"} in findings


def test_detects_multiple_manifests(tmp_path):
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")
    (tmp_path / "go.mod").write_text("", encoding="utf-8")
    findings = dependency_scanner.scan(tmp_path)
    ecosystems = {f["ecosystem"] for f in findings}
    assert ecosystems == {"python", "go"}


def test_no_manifests_returns_empty_list(tmp_path):
    assert dependency_scanner.scan(tmp_path) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_dependency_scanner.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/evidence/dependency_scanner.py
"""Detect dependency manifest files that hint at technology choices."""
from pathlib import Path

MANIFEST_FILES = {
    "package.json": "npm",
    "pyproject.toml": "python",
    "requirements.txt": "python",
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    "go.mod": "go",
    "Cargo.toml": "cargo",
}


def scan(root: Path) -> list:
    findings = []
    for filename, ecosystem in MANIFEST_FILES.items():
        path = root / filename
        if path.is_file():
            findings.append({"ecosystem": ecosystem, "path": filename})
    return findings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_dependency_scanner.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/evidence/dependency_scanner.py tests/unit/test_dependency_scanner.py
git commit -m "feat: add dependency manifest evidence scanner"
```

---

### Task 8: `commands/discover.py` — repository evidence collection

**Files:**
- Create: `skills/adr-toolkit/scripts/commands/discover.py`
- Test: `tests/unit/test_discover.py`

**Interfaces:**
- Consumes: `scripts.evidence.dependency_scanner.scan` (Task 7).
- Produces: `run(args) -> dict` where `args.root` defaults to `"."`. Return shape: `{"ok": True, "operation": "discover", "root": str, "dependencies": list, "warnings": list}`. Used by Task 14 (CLI) and Task 17 (fixture test).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_discover.py
from types import SimpleNamespace

from scripts.commands import discover


def test_discover_reports_dependency_findings(tmp_path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    result = discover.run(SimpleNamespace(root=str(tmp_path)))
    assert result["ok"] is True
    assert {"ecosystem": "npm", "path": "package.json"} in result["dependencies"]


def test_discover_on_empty_repo_reports_no_dependencies(tmp_path):
    result = discover.run(SimpleNamespace(root=str(tmp_path)))
    assert result["dependencies"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_discover.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/commands/discover.py
"""Scan the repository for evidence of existing conventions and past decisions."""
from pathlib import Path

from scripts.evidence import dependency_scanner


def run(args) -> dict:
    root = Path(getattr(args, "root", ".")).resolve()
    dependencies = dependency_scanner.scan(root)

    return {
        "ok": True,
        "operation": "discover",
        "root": str(root),
        "dependencies": dependencies,
        "warnings": [],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_discover.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/discover.py tests/unit/test_discover.py
git commit -m "feat: add discover command orchestrating evidence scanners"
```

---

### Task 9: MADR templates (minimal and full)

**Files:**
- Create: `skills/adr-toolkit/templates/madr-minimal.md`
- Create: `skills/adr-toolkit/templates/madr-full.md`
- Test: `tests/unit/test_templates.py`

**Interfaces:**
- Consumes: nothing.
- Produces: two template files referenced by `SKILL.md` (Task 15) when the agent drafts ADR bodies. Not imported by Python code.

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_templates.py -v`
Expected: FAIL — files don't exist.

- [ ] **Step 3: Write the template files**

```markdown
<!-- skills/adr-toolkit/templates/madr-minimal.md -->
# {title}

## Context and Problem Statement

{problem and constraints}

## Considered Options

* {option one}
* {option two}

## Decision Outcome

Chosen option: **{chosen option}**, because {rationale}.

## Consequences

* Good: {positive consequence}
* Bad: {negative consequence}

## Confirmation

{how implementation will be verified}

## Revisit Triggers

* {condition that should reopen the decision}
```

```markdown
<!-- skills/adr-toolkit/templates/madr-full.md -->
# {title}

## Context and Problem Statement

{problem and constraints}

## Decision Drivers

* {driver one}
* {driver two}

## Considered Options

* {option one}
* {option two}
* {option three}

## Decision Outcome

Chosen option: **{chosen option}**, because {rationale}.

### Consequences

* Good: {positive consequence}
* Bad: {negative consequence}

### Confirmation

{how implementation will be verified}

## Pros and Cons of the Options

### {option one}

* Good, because {argument}
* Bad, because {argument}

### {option two}

* Good, because {argument}
* Bad, because {argument}

## Revisit Triggers

* {condition that should reopen the decision}
```

Delete `skills/adr-toolkit/templates/.gitkeep`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_templates.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git rm skills/adr-toolkit/templates/.gitkeep
git add skills/adr-toolkit/templates/madr-minimal.md skills/adr-toolkit/templates/madr-full.md \
        tests/unit/test_templates.py
git commit -m "feat: add minimal and full MADR templates"
```

---

### Task 10: `commands/init.py` — scaffold a new ADR directory

**Files:**
- Create: `skills/adr-toolkit/scripts/commands/init.py`
- Test: `tests/unit/test_init.py`

**Interfaces:**
- Consumes: `skills/adr-toolkit/templates/madr-minimal.md` (Task 9, copied as-is into the new directory).
- Produces: `run(args) -> dict` where `args` has `.dir` (str) and optional `.dry_run` (bool). Return shape on success: `{"ok": True, "operation": "init", "dry_run": bool, "created"/"would_create": list}`; on conflict: `{"ok": False, "operation": "init", "errors": [{"code": "ADR_DIRECTORY_NOT_EMPTY", "path": str}]}`. Used by Task 14 (CLI) and Task 17 (fixture test).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_init.py
from types import SimpleNamespace

from scripts.commands import init


def test_dry_run_reports_would_create_without_writing(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    result = init.run(SimpleNamespace(dir=str(adr_dir), dry_run=True))
    assert result["ok"] is True
    assert result["dry_run"] is True
    assert not adr_dir.exists()


def test_creates_directory_template_and_first_adr(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    result = init.run(SimpleNamespace(dir=str(adr_dir), dry_run=False))
    assert result["ok"] is True
    assert (adr_dir / "adr-template.md").is_file()
    first_adr = adr_dir / "0001-record-architecture-decisions.md"
    assert first_adr.is_file()
    content = first_adr.read_text(encoding="utf-8")
    assert "id: ADR-0001" in content
    assert "status: accepted" in content


def test_refuses_to_run_on_non_empty_directory(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "existing.md").write_text("x", encoding="utf-8")

    result = init.run(SimpleNamespace(dir=str(adr_dir), dry_run=False))
    assert result["ok"] is False
    assert result["errors"][0]["code"] == "ADR_DIRECTORY_NOT_EMPTY"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_init.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/commands/init.py
"""Scaffold an ADR directory for a repository that has none yet."""
import shutil
from datetime import date
from pathlib import Path

TEMPLATE_SOURCE = Path(__file__).resolve().parent.parent.parent / "templates" / "madr-minimal.md"

INITIAL_ADR_BODY = """# Record architecture decisions

## Context and Problem Statement

We need a consistent way to capture and communicate significant
architectural decisions so future contributors (human or agent) can find
the reasoning behind them.

## Considered Options

* No formal record, rely on commit messages and memory
* Wiki or external documentation tool
* Architecture Decision Records stored alongside the code

## Decision Outcome

Chosen option: **Architecture Decision Records stored alongside the code**, because they version with the code, stay close to what they describe, and are readable by both humans and coding agents.

## Consequences

* Good: decisions and their rationale are discoverable in the repository itself.
* Bad: requires discipline to keep records up to date as decisions evolve.

## Confirmation

* [ ] `docs/decisions/` exists with this file, a template, and an index.

## Revisit Triggers

* The team adopts a different documentation system project-wide.
"""


def run(args) -> dict:
    adr_dir = Path(args.dir)
    dry_run = getattr(args, "dry_run", False)

    if adr_dir.exists() and any(adr_dir.iterdir()):
        return {
            "ok": False,
            "operation": "init",
            "errors": [{"code": "ADR_DIRECTORY_NOT_EMPTY", "path": str(adr_dir)}],
        }

    would_create = [
        str(adr_dir),
        str(adr_dir / "adr-template.md"),
        str(adr_dir / "0001-record-architecture-decisions.md"),
    ]

    if dry_run:
        return {"ok": True, "operation": "init", "dry_run": True, "would_create": would_create}

    adr_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE_SOURCE, adr_dir / "adr-template.md")

    frontmatter_block = (
        "---\n"
        "id: ADR-0001\n"
        "title: Record architecture decisions\n"
        "status: accepted\n"
        f"date: {date.today().isoformat()}\n"
        "decision_makers: []\n"
        "related: []\n"
        "affected_paths:\n"
        "  - docs/decisions/\n"
        "tags:\n"
        "  - process\n"
        "retrospective: false\n"
        "---\n\n"
    )
    (adr_dir / "0001-record-architecture-decisions.md").write_text(
        frontmatter_block + INITIAL_ADR_BODY, encoding="utf-8"
    )

    return {"ok": True, "operation": "init", "dry_run": False, "created": would_create}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_init.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/init.py tests/unit/test_init.py
git commit -m "feat: add init command to scaffold ADR directory"
```

---

### Task 11: `commands/create.py` — write a new ADR from an approved draft

**Files:**
- Create: `skills/adr-toolkit/scripts/commands/create.py`
- Test: `tests/unit/test_create.py`

**Interfaces:**
- Consumes: `scripts.core.frontmatter.serialize` (Task 2), `scripts.core.identifiers.{next_id, slugify, format_filename}` (Task 3), `scripts.core.schema.validate_frontmatter` (Task 5).
- Produces: `run(args) -> dict` where `args` has `.input` (path to draft JSON), `.dir` (ADR directory), optional `.dry_run`. The draft JSON must have `title`, `status`, `body` (pre-rendered markdown from the agent); optional `date`, `decision_makers`, `related`, `affected_paths`, `tags`, `retrospective`. Return shape on success: `{"ok": True, "operation": "create", "dry_run": bool, "created"/"would_create": str, "id": str}`. Used by Task 14 (CLI) and Task 17 (fixture test).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_create.py
import json
from pathlib import Path
from types import SimpleNamespace

from scripts.commands import create


def _write_draft(tmp_path, **overrides):
    draft = {
        "title": "Use Kafka for domain events",
        "status": "accepted",
        "body": "# Use Kafka for domain events\n\nBody text.\n",
    }
    draft.update(overrides)
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps(draft), encoding="utf-8")
    return draft_path


def test_creates_file_with_next_id_and_valid_frontmatter(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = _write_draft(tmp_path)

    result = create.run(SimpleNamespace(input=str(draft_path), dir=str(adr_dir), dry_run=False))

    assert result["ok"] is True
    assert result["id"] == "ADR-0001"
    created_file = Path(result["created"])
    assert created_file.name == "0001-use-kafka-for-domain-events.md"
    assert "status: accepted" in created_file.read_text(encoding="utf-8")


def test_next_id_accounts_for_existing_adrs(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-existing.md").write_text("x", encoding="utf-8")
    draft_path = _write_draft(tmp_path)

    result = create.run(SimpleNamespace(input=str(draft_path), dir=str(adr_dir), dry_run=False))

    assert result["id"] == "ADR-0002"


def test_dry_run_does_not_write_file(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = _write_draft(tmp_path)

    result = create.run(SimpleNamespace(input=str(draft_path), dir=str(adr_dir), dry_run=True))

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert list(adr_dir.iterdir()) == []


def test_missing_required_draft_field_is_an_error(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps({"title": "Missing status and body"}), encoding="utf-8")

    result = create.run(SimpleNamespace(input=str(draft_path), dir=str(adr_dir), dry_run=False))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "MISSING_DRAFT_FIELD"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_create.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/commands/create.py
"""Assign the next ADR ID and write a new ADR file from an approved draft."""
import json
from datetime import date
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.schema import validate_frontmatter

REQUIRED_DRAFT_FIELDS = {"title", "status", "body"}


def run(args) -> dict:
    draft_path = Path(args.input)
    adr_dir = Path(args.dir)
    dry_run = getattr(args, "dry_run", False)

    draft = json.loads(draft_path.read_text(encoding="utf-8"))
    missing = REQUIRED_DRAFT_FIELDS - draft.keys()
    if missing:
        return {
            "ok": False,
            "operation": "create",
            "errors": [{"code": "MISSING_DRAFT_FIELD", "fields": sorted(missing)}],
        }

    adr_dir.mkdir(parents=True, exist_ok=True)
    next_num = identifiers.next_id(adr_dir)
    slug = identifiers.slugify(draft["title"])
    filename = identifiers.format_filename(next_num, slug)
    target = adr_dir / filename

    if target.exists():
        return {
            "ok": False,
            "operation": "create",
            "errors": [{"code": "FILE_ALREADY_EXISTS", "path": str(target)}],
        }

    frontmatter_data = {
        "id": f"ADR-{next_num:04d}",
        "title": draft["title"],
        "status": draft["status"],
        "date": draft.get("date") or date.today().isoformat(),
        "decision_makers": draft.get("decision_makers", []),
        "related": draft.get("related", []),
        "affected_paths": draft.get("affected_paths", []),
        "tags": draft.get("tags", []),
        "retrospective": draft.get("retrospective", False),
    }

    schema_errors = validate_frontmatter(frontmatter_data)
    if schema_errors:
        return {
            "ok": False,
            "operation": "create",
            "errors": [{"code": "SCHEMA_ERROR", "detail": e} for e in schema_errors],
        }

    content = fm.serialize(frontmatter_data, draft["body"].strip() + "\n")

    if dry_run:
        return {"ok": True, "operation": "create", "dry_run": True, "would_create": str(target)}

    target.write_text(content, encoding="utf-8")

    return {
        "ok": True,
        "operation": "create",
        "dry_run": False,
        "created": str(target),
        "id": frontmatter_data["id"],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_create.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/create.py tests/unit/test_create.py
git commit -m "feat: add create command to write approved ADR drafts"
```

---

### Task 12: `commands/index.py` — multi-view decision log

**Files:**
- Create: `skills/adr-toolkit/scripts/commands/index.py`
- Test: `tests/unit/test_index.py`

**Interfaces:**
- Consumes: `scripts.core.frontmatter.parse` (Task 2), `scripts.core.identifiers.parse_filename` (Task 3).
- Produces: `run(args) -> dict` where `args.dir` is the ADR directory. Return shape: `{"ok": True, "operation": "index", "count": int, "path": str}`. Writes `README.md` inside the ADR directory with By-status / By-tag / By-affected-path / Chronological sections. Used by Task 14 (CLI) and Task 17 (fixture test).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_index.py
from types import SimpleNamespace

from scripts.commands import index


def _write_adr(adr_dir, filename, *, id_, title, status, date, tags, affected_paths):
    tags_block = "\n".join(f"  - {t}" for t in tags) or None
    paths_block = "\n".join(f"  - {p}" for p in affected_paths) or None
    text = (
        "---\n"
        f"id: {id_}\n"
        f"title: {title}\n"
        f"status: {status}\n"
        f"date: {date}\n"
        "decision_makers: []\n"
        "related: []\n"
        f"affected_paths:\n{paths_block}\n"
        f"tags:\n{tags_block}\n"
        "retrospective: false\n"
        "---\n\n"
        f"# {title}\n"
    )
    (adr_dir / filename).write_text(text, encoding="utf-8")


def test_index_generates_readme_with_all_views(tmp_path):
    adr_dir = tmp_path
    _write_adr(
        adr_dir, "0001-use-kafka.md",
        id_="ADR-0001", title="Use Kafka", status="accepted", date="2026-08-01",
        tags=["architecture"], affected_paths=["src/events/"],
    )
    _write_adr(
        adr_dir, "0002-use-postgres.md",
        id_="ADR-0002", title="Use Postgres", status="proposed", date="2026-08-15",
        tags=["architecture", "data"], affected_paths=["src/db/"],
    )

    result = index.run(SimpleNamespace(dir=str(adr_dir)))

    assert result["ok"] is True
    assert result["count"] == 2
    readme = (adr_dir / "README.md").read_text(encoding="utf-8")
    assert "## By status" in readme
    assert "## By tag" in readme
    assert "## By affected path" in readme
    assert "## Chronological" in readme
    assert "ADR-0001" in readme and "ADR-0002" in readme
    assert "`src/events/`" in readme


def test_index_skips_readme_and_template_files(tmp_path):
    (tmp_path / "adr-template.md").write_text("not an ADR", encoding="utf-8")
    result = index.run(SimpleNamespace(dir=str(tmp_path)))
    assert result["count"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_index.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/commands/index.py
"""Regenerate the multi-view ADR index (README.md) for a decision directory."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers

SKIP_FILES = {"README.md", "adr-template.md"}


def run(args) -> dict:
    adr_dir = Path(args.dir)
    entries = []

    for entry in sorted(adr_dir.glob("*.md")):
        if entry.name in SKIP_FILES:
            continue
        parsed = identifiers.parse_filename(entry.name)
        if parsed is None:
            continue
        data, _ = fm.parse(entry.read_text(encoding="utf-8"))
        entries.append({
            "id": data.get("id", f"ADR-{parsed[0]:04d}"),
            "filename": entry.name,
            "title": data.get("title", parsed[1]),
            "status": data.get("status", "unknown"),
            "date": data.get("date", ""),
            "tags": data.get("tags", []),
            "affected_paths": data.get("affected_paths", []),
        })

    (adr_dir / "README.md").write_text(_render(entries), encoding="utf-8")

    return {"ok": True, "operation": "index", "count": len(entries), "path": str(adr_dir / "README.md")}


def _render(entries: list) -> str:
    lines = ["# Decision Log", ""]

    lines.append("## By status")
    lines.append("")
    by_status: dict = {}
    for entry in entries:
        by_status.setdefault(entry["status"], []).append(entry)
    for status in sorted(by_status):
        lines.append(f"### {status.capitalize()}")
        for entry in sorted(by_status[status], key=lambda e: e["filename"]):
            lines.append(f"- [{entry['id']} — {entry['title']}]({entry['filename']})")
        lines.append("")

    lines.append("## By tag")
    lines.append("")
    by_tag: dict = {}
    for entry in entries:
        for tag in entry["tags"]:
            by_tag.setdefault(tag, []).append(entry)
    for tag in sorted(by_tag):
        lines.append(f"### {tag}")
        for entry in sorted(by_tag[tag], key=lambda e: e["filename"]):
            lines.append(f"- [{entry['id']} — {entry['title']}]({entry['filename']})")
        lines.append("")

    lines.append("## By affected path")
    lines.append("")
    by_path: dict = {}
    for entry in entries:
        for path in entry["affected_paths"]:
            by_path.setdefault(path, []).append(entry)
    for path in sorted(by_path):
        lines.append(f"### `{path}`")
        for entry in sorted(by_path[path], key=lambda e: e["filename"]):
            lines.append(f"- [{entry['id']} — {entry['title']}]({entry['filename']})")
        lines.append("")

    lines.append("## Chronological (newest first)")
    lines.append("")
    for entry in sorted(entries, key=lambda e: e["date"], reverse=True):
        lines.append(f"- {entry['date']} — [{entry['id']} — {entry['title']}]({entry['filename']})")

    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_index.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/index.py tests/unit/test_index.py
git commit -m "feat: add multi-view decision log index command"
```

---

### Task 13: `commands/validate.py` — structural integrity checks

**Files:**
- Create: `skills/adr-toolkit/scripts/commands/validate.py`
- Test: `tests/unit/test_validate.py`

**Interfaces:**
- Consumes: `scripts.core.frontmatter.parse` (Task 2), `scripts.core.identifiers.parse_filename` (Task 3), `scripts.core.schema.validate_frontmatter` (Task 5).
- Produces: `run(args) -> dict` where `args.dir` is the ADR directory. Return shape: `{"ok": bool, "operation": "validate", "checked": int, "errors": list}`. Used by Task 14 (CLI) and Task 17 (fixture test).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_validate.py
from types import SimpleNamespace

from scripts.commands import validate

VALID_ADR = (
    "---\n"
    "id: ADR-0001\n"
    "title: Record architecture decisions\n"
    "status: accepted\n"
    "date: 2026-08-29\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths:\n"
    "  - docs/decisions/\n"
    "tags:\n"
    "  - process\n"
    "retrospective: false\n"
    "---\n\n"
    "# Record architecture decisions\n"
)


def test_valid_directory_passes(tmp_path):
    (tmp_path / "0001-record-architecture-decisions.md").write_text(VALID_ADR, encoding="utf-8")
    result = validate.run(SimpleNamespace(dir=str(tmp_path)))
    assert result["ok"] is True
    assert result["checked"] == 1
    assert result["errors"] == []


def test_duplicate_ids_are_reported(tmp_path):
    (tmp_path / "0001-a.md").write_text(VALID_ADR, encoding="utf-8")
    duplicate = VALID_ADR.replace("title: Record architecture decisions", "title: A duplicate")
    (tmp_path / "0002-b.md").write_text(duplicate, encoding="utf-8")

    result = validate.run(SimpleNamespace(dir=str(tmp_path)))

    assert result["ok"] is False
    assert any(e["code"] == "DUPLICATE_ADR_ID" for e in result["errors"])


def test_broken_related_link_is_reported(tmp_path):
    broken = VALID_ADR.replace("related: []", "related:\n  - ADR-0099")
    (tmp_path / "0001-a.md").write_text(broken, encoding="utf-8")

    result = validate.run(SimpleNamespace(dir=str(tmp_path)))

    assert result["ok"] is False
    assert any(e["code"] == "BROKEN_RELATED_LINK" for e in result["errors"])


def test_bad_filename_is_reported(tmp_path):
    (tmp_path / "not-a-valid-name.md").write_text(VALID_ADR, encoding="utf-8")
    result = validate.run(SimpleNamespace(dir=str(tmp_path)))
    assert any(e["code"] == "BAD_FILENAME" for e in result["errors"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_validate.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/commands/validate.py
"""Validate ADR directory structural integrity: IDs, frontmatter, and links."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.schema import validate_frontmatter

SKIP_FILES = {"README.md", "adr-template.md"}


def run(args) -> dict:
    adr_dir = Path(args.dir)
    errors = []

    adr_files = sorted(p for p in adr_dir.glob("*.md") if p.name not in SKIP_FILES)

    parsed_entries = []
    seen_ids: dict = {}

    for path in adr_files:
        if identifiers.parse_filename(path.name) is None:
            errors.append({"code": "BAD_FILENAME", "file": path.name})
            continue

        try:
            data, _ = fm.parse(path.read_text(encoding="utf-8"))
        except fm.FrontmatterError as exc:
            errors.append({"code": "BAD_FRONTMATTER", "file": path.name, "detail": str(exc)})
            continue

        for detail in validate_frontmatter(data):
            errors.append({"code": "SCHEMA_ERROR", "file": path.name, "detail": detail})

        adr_id = data.get("id")
        if adr_id:
            if adr_id in seen_ids:
                errors.append({"code": "DUPLICATE_ADR_ID", "files": [seen_ids[adr_id], path.name]})
            else:
                seen_ids[adr_id] = path.name

        parsed_entries.append((path.name, data))

    known_ids = set(seen_ids.keys())
    for filename, data in parsed_entries:
        for related_id in data.get("related", []):
            if related_id not in known_ids:
                errors.append({"code": "BROKEN_RELATED_LINK", "file": filename, "related_id": related_id})

    return {"ok": not errors, "operation": "validate", "checked": len(adr_files), "errors": errors}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_validate.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/validate.py tests/unit/test_validate.py
git commit -m "feat: add validate command for ADR structural integrity"
```

---

### Task 14: `scripts/adr.py` — single CLI entrypoint

**Files:**
- Create: `skills/adr-toolkit/scripts/adr.py`
- Test: `tests/integration/test_cli.py`

**Interfaces:**
- Consumes: `scripts.commands.{preflight, discover, init, create, index, validate}.run` (Tasks 6, 8, 10, 11, 12, 13).
- Produces: an executable script (`python scripts/adr.py <subcommand> [--json] ...`) printing one JSON object to stdout and exiting 0 on `ok: true`, 1 otherwise. This is what `SKILL.md` (Task 15) and the fixture test (Task 17) actually invoke.

- [ ] **Step 1: Write the failing test**

```python
# tests/integration/test_cli.py
import json
import subprocess
import sys
from pathlib import Path

ADR_PY = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit" / "scripts" / "adr.py"


def _run(args, cwd):
    return subprocess.run(
        [sys.executable, str(ADR_PY), *args], cwd=cwd, capture_output=True, text=True,
    )


def test_preflight_returns_valid_json(tmp_path):
    result = _run(["preflight", "--json"], cwd=tmp_path)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["operation"] == "preflight"
    assert payload["ok"] is True


def test_init_then_validate_round_trip(tmp_path):
    init_result = _run(["init", "--dir", "docs/decisions", "--json"], cwd=tmp_path)
    assert init_result.returncode == 0

    validate_result = _run(["validate", "--dir", "docs/decisions", "--json"], cwd=tmp_path)
    payload = json.loads(validate_result.stdout)
    assert validate_result.returncode == 0
    assert payload["ok"] is True
    assert payload["checked"] == 1


def test_unknown_subcommand_exits_nonzero(tmp_path):
    result = _run(["not-a-real-command"], cwd=tmp_path)
    assert result.returncode != 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/integration/test_cli.py -v`
Expected: FAIL — `scripts/adr.py` doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
#!/usr/bin/env python3
# skills/adr-toolkit/scripts/adr.py
"""Single entrypoint for all ADR Toolkit deterministic operations."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.commands import preflight, discover, init, create, index, validate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="adr.py")
    sub = parser.add_subparsers(dest="operation", required=True)

    p_preflight = sub.add_parser("preflight")
    p_preflight.add_argument("--json", action="store_true")
    p_preflight.add_argument("--root", default=".")

    p_discover = sub.add_parser("discover")
    p_discover.add_argument("--json", action="store_true")
    p_discover.add_argument("--root", default=".")

    p_init = sub.add_parser("init")
    p_init.add_argument("--dir", default="docs/decisions")
    p_init.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_init.add_argument("--json", action="store_true")

    p_create = sub.add_parser("create")
    p_create.add_argument("--input", required=True)
    p_create.add_argument("--dir", default="docs/decisions")
    p_create.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_create.add_argument("--json", action="store_true")

    p_index = sub.add_parser("index")
    p_index.add_argument("--dir", default="docs/decisions")
    p_index.add_argument("--json", action="store_true")

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--dir", default="docs/decisions")
    p_validate.add_argument("--json", action="store_true")

    return parser


HANDLERS = {
    "preflight": preflight.run,
    "discover": discover.run,
    "init": init.run,
    "create": create.run,
    "index": index.run,
    "validate": validate.run,
}


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = HANDLERS[args.operation](args)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/integration/test_cli.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/adr.py tests/integration/test_cli.py
git commit -m "feat: add single CLI entrypoint dispatching ADR subcommands"
```

---

### Task 15: `SKILL.md` and INIT-supporting references

**Files:**
- Create: `skills/adr-toolkit/SKILL.md`
- Create: `skills/adr-toolkit/references/lifecycle.md`
- Create: `skills/adr-toolkit/references/madr-guide.md`
- Test: `tests/unit/test_skill_manifest.py`

**Interfaces:**
- Consumes: `scripts.core.frontmatter.parse` (Task 2, reused by the test to check `SKILL.md`'s own frontmatter).
- Produces: the skill's user-facing contract. Consumed by Task 16 (Claude adapter) and by any harness that loads this skill.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_skill_manifest.py
from pathlib import Path

from scripts.core import frontmatter as fm

SKILL_MD = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit" / "SKILL.md"
REFERENCES = SKILL_MD.parent / "references"


def test_skill_md_frontmatter_has_required_fields():
    data, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    assert data["name"] == "adr-toolkit"
    assert data["user-invocable"] is True
    assert "description" in data
    assert "version" in data


def test_skill_md_documents_the_workflow_stages():
    _, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    for stage in ["PREFLIGHT", "DISCOVER", "CLASSIFY", "ASK-IF-NEEDED", "PLAN", "CONFIRM", "MUTATE", "VALIDATE", "REPORT"]:
        assert stage in body


def test_skill_md_separates_init_and_discover_operations():
    _, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    assert "## INIT" in body
    assert "## DISCOVER" in body
    assert "## What belongs in an ADR" in body


def test_skill_md_requires_evidence_inference_separation_for_retrospective_adrs():
    _, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    assert "Confirmed Evidence" in body
    assert "Inferred Rationale" in body
    assert "## Unknown" in body


def test_reference_files_exist():
    assert (REFERENCES / "lifecycle.md").is_file()
    assert (REFERENCES / "madr-guide.md").is_file()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_skill_manifest.py -v`
Expected: FAIL — files don't exist.

- [ ] **Step 3: Write the content**

```markdown
<!-- skills/adr-toolkit/SKILL.md -->
---
name: adr-toolkit
description: >
  Initialize, record, and check Architecture Decision Records by inspecting
  the repository and existing decisions before asking questions.
user-invocable: true
version: 0.1.0
---

# ADR Toolkit

## Workflow contract

Every operation follows the same nine stages:

```text
PREFLIGHT
→ DISCOVER
→ CLASSIFY
→ ASK-IF-NEEDED
→ PLAN
→ CONFIRM
→ MUTATE
→ VALIDATE
→ REPORT
```

## INIT (scaffolding only)

Use INIT when a repository has no ADR directory yet. INIT does not mine
history — it only sets up the structure. Run DISCOVER afterward (or any
time later) to recover past decisions.

1. **PREFLIGHT** — run `python scripts/adr.py preflight --json`. If
   `existing_adr_directory` is set, stop and tell the user an ADR directory
   already exists; do not scaffold a second one.
2. **CONFIRM** — show the user the exact directory that will be created,
   before writing anything.
3. **MUTATE** — run `python scripts/adr.py init --dir docs/decisions` to
   scaffold the directory, template, and ADR-0001.
4. **VALIDATE** — run `python scripts/adr.py validate --dir docs/decisions --json`
   and `python scripts/adr.py index --dir docs/decisions --json`.
5. **REPORT** — tell the user INIT is done and that they can run DISCOVER
   next if they want to recover past decisions from the repository's
   history.

## DISCOVER (past-decision recovery)

Use DISCOVER on a repository that already has an ADR directory (run INIT
first if it doesn't). DISCOVER can be run once right after INIT, skipped
entirely, or re-run later to mine more of the history incrementally.

1. **PREFLIGHT** — run `python scripts/adr.py preflight --json`. If
   `existing_adr_directory` is `null`, stop and tell the user to run INIT
   first.
2. **GATHER EVIDENCE** — run `python scripts/adr.py discover --json` from
   the repository root. Read the `dependencies` list; each entry is
   candidate evidence for a past architectural decision (e.g. `pom.xml`
   suggests a JVM build-tool decision was made, even if undocumented).
3. **CLASSIFY** — for each finding, decide whether it looks structural (a
   database driver, a message broker, a web framework) versus routine
   tooling (a linter, a test runner), using the table below. Only
   structural choices are candidates.
4. **ASK-IF-NEEDED** — for each candidate, ask the user at most one
   question: why was this chosen, only if the reason is not evident from
   comments, README, or commit history. Do not ask about anything
   `discover` already reported as a fact.
5. **PLAN** — draft a `retrospective: true` MADR body for each ADR the user
   wants recorded, following `templates/madr-minimal.md` (see
   `references/madr-guide.md` for when to use the full template instead).
   Every retrospective body MUST contain three separate subsections, never
   merged into one narrative:

   ```markdown
   ## Confirmed Evidence

   * {only facts `discover` or the user's own words actually established}

   ## Inferred Rationale

   * {the agent's best guess at *why*, explicitly labeled as a guess}

   ## Unknown

   * {anything about the original decision that cannot be recovered from this repository}
   ```

6. **CONFIRM** — show the user each candidate's title, confirmed evidence,
   and inferred rationale before writing anything; the user can drop any
   candidate.
7. **MUTATE** — for each approved candidate, write a draft JSON file
   (`title`, `status`, `body` — body includes the three-part structure
   above — plus any of `date`/`decision_makers`/`related`/
   `affected_paths`/`tags`/`retrospective`) and run
   `python scripts/adr.py create --input <draft.json> --dir docs/decisions`.
8. **VALIDATE** — same as INIT step 4. If validate reports errors, fix the
   draft and re-run `create` — never hand-edit the generated file to patch
   a validation error.
9. **REPORT** — tell the user what was created, in this order: facts
   found, judgment, questions asked, files created, validation result,
   remaining uncertainty.

## What belongs in an ADR

Not every structural-looking finding deserves a new file. Apply this table
during CLASSIFY, in both INIT/DISCOVER and (once built) RECORD:

| Content | Where it belongs |
|---|---|
| Structural, long-lived decision | ADR |
| Feature implementation detail | Pull request |
| Routine code-change rationale | Commit message |
| Usage/behavior explanation | README or docs |
| Incident/outage response | Incident report / postmortem |
| A rule that must hold going forward | ADR's Implementation Constraints |

## Prohibited

- Creating `docs/decisions/` when `preflight` already found one.
- Running DISCOVER when `preflight` reports no ADR directory — tell the
  user to run INIT first instead.
- Writing any ADR file before the user has seen and approved its title,
  problem, and decision.
- Marking a retrospective ADR `status: accepted` without the user
  confirming the reconstruction is accurate.
- Guessing a dependency's purpose instead of asking, when it's not evident
  from the repository.
- Merging Confirmed Evidence, Inferred Rationale, and Unknown into a single
  undifferentiated narrative for a retrospective ADR.

## Script reference

All mutating and validating operations are deterministic scripts under
`scripts/`; this skill never re-implements ID assignment, file writes, or
schema validation in prose — it only decides what to ask and what to draft.

RECORD and CHECK workflows are not yet implemented (see `project-roadmap.md`
in the repository root and the design spec this skill is built from).
```

```markdown
<!-- skills/adr-toolkit/references/lifecycle.md -->
# ADR Lifecycle Reference

## Statuses

- `proposed` — drafted, not yet approved by a human.
- `accepted` — approved and currently in force.
- `rejected` — considered and explicitly declined.
- `deprecated` — no longer recommended, no direct replacement.
- `superseded` — replaced by a specific later ADR (`superseded_by` must be set).

## Allowed transitions

```text
proposed   -> accepted | rejected
accepted   -> deprecated | superseded
rejected   -> (terminal)
deprecated -> (terminal)
superseded -> (terminal)
```

`scripts/core/lifecycle.py` enforces this table. If a user asks for a
transition that isn't in it, confirm they understand it's non-standard
before doing anything, and never write a status that violates the table.
```

```markdown
<!-- skills/adr-toolkit/references/madr-guide.md -->
# MADR Template Guide

## When to use `madr-minimal.md`

- The decision has two or fewer realistic alternatives.
- No conflicting quality attributes need a comparison table.
- The project is small enough that a short record is genuinely sufficient.

## When to use `madr-full.md`

- Three or more alternatives were seriously considered.
- Different options trade off against each other on quality attributes
  (e.g. latency vs. operational complexity).
- The decision affects multiple teams, services, or systems.

## Section meaning

- **Context and Problem Statement** — the forces and constraints that made
  a decision necessary; not a restatement of the chosen solution.
- **Considered Options** — every realistic option actually evaluated, not
  a strawman list.
- **Decision Outcome** — the chosen option and the primary reason, stated
  as a single sentence a newcomer could quote.
- **Consequences** — both the benefit and the accepted cost; a decision
  with no listed downside has not been examined honestly.
- **Confirmation** — how someone (human or agent) can verify the decision
  is actually being followed in the code today.
- **Revisit Triggers** — concrete conditions, not vague ones like "if
  requirements change."
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_skill_manifest.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git rm skills/adr-toolkit/references/.gitkeep
git add skills/adr-toolkit/SKILL.md skills/adr-toolkit/references/lifecycle.md \
        skills/adr-toolkit/references/madr-guide.md tests/unit/test_skill_manifest.py
git commit -m "feat: add SKILL.md workflow contract and INIT reference docs"
```

---

### Task 16: Claude Code adapter manifest

**Files:**
- Create: `adapters/claude/.claude-plugin/plugin.json`
- Create: `adapters/claude/marketplace.json`
- Test: `tests/unit/test_claude_adapter.py`

**Interfaces:**
- Consumes: `skills/adr-toolkit/SKILL.md` (Task 15) — the manifest's `skills` path must resolve to that directory.
- Produces: an installable Claude Code plugin. No Python interface — this task is manifest content only.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_claude_adapter.py
import json
from pathlib import Path

ADAPTER_DIR = Path(__file__).resolve().parent.parent.parent / "adapters" / "claude"


def test_plugin_manifest_has_required_keys():
    manifest = json.loads((ADAPTER_DIR / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "adr-toolkit"
    assert "version" in manifest
    assert manifest["skills"], "plugin.json must list at least one skill path"


def test_plugin_manifest_skill_path_resolves_to_real_skill():
    manifest = json.loads((ADAPTER_DIR / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    skill_path = (ADAPTER_DIR / ".claude-plugin" / manifest["skills"][0]).resolve()
    assert skill_path.is_dir()
    assert (skill_path / "SKILL.md").is_file()


def test_marketplace_manifest_lists_the_plugin():
    marketplace = json.loads((ADAPTER_DIR / "marketplace.json").read_text(encoding="utf-8"))
    names = [p["name"] for p in marketplace["plugins"]]
    assert "adr-toolkit" in names
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_claude_adapter.py -v`
Expected: FAIL — manifests don't exist.

- [ ] **Step 3: Write the manifests**

```json
// adapters/claude/.claude-plugin/plugin.json
{
  "name": "adr-toolkit",
  "version": "0.1.0",
  "description": "Initialize, record, and check Architecture Decision Records by inspecting the repository before asking questions.",
  "skills": [
    "../../../skills/adr-toolkit"
  ]
}
```

```json
// adapters/claude/marketplace.json
{
  "name": "adr-toolkit-marketplace",
  "plugins": [
    {
      "name": "adr-toolkit",
      "source": "./",
      "description": "Agent-native ADR toolkit: inspect the repo, ask only what code can't answer, record and check architecture decisions."
    }
  ]
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_claude_adapter.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add adapters/claude/.claude-plugin/plugin.json adapters/claude/marketplace.json \
        tests/unit/test_claude_adapter.py
git commit -m "feat: add Claude Code adapter manifest for adr-toolkit skill"
```

---

### Task 17: End-to-end INIT fixture and golden test

**Files:**
- Create: `tests/fixtures/init_no_adr_js_project/package.json`
- Create: `tests/integration/test_init_workflow.py`

**Interfaces:**
- Consumes: `scripts/adr.py` (Task 14) via subprocess, exercising `preflight`, `discover`, `init`, `validate`, `index` end to end.
- Produces: the golden proof that the INIT workflow this plan builds actually works on a realistic repository, not just in isolated unit tests.

- [ ] **Step 1: Write the failing test**

```json
// tests/fixtures/init_no_adr_js_project/package.json
{
  "name": "sample-app",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.18.0"
  }
}
```

```python
# tests/integration/test_init_workflow.py
import json
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "init_no_adr_js_project"
ADR_PY = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit" / "scripts" / "adr.py"


def _run(args, cwd):
    result = subprocess.run(
        [sys.executable, str(ADR_PY), *args], cwd=cwd, capture_output=True, text=True,
    )
    assert result.returncode in (0, 1), result.stderr
    return json.loads(result.stdout)


def test_full_init_flow_on_js_fixture(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)

    preflight = _run(["preflight", "--json"], cwd=repo)
    assert preflight["ok"] is True
    assert preflight["existing_adr_directory"] is None

    discovered = _run(["discover", "--json"], cwd=repo)
    assert {"ecosystem": "npm", "path": "package.json"} in discovered["dependencies"]

    init_result = _run(["init", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert init_result["ok"] is True

    validate_result = _run(["validate", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert validate_result["ok"] is True
    assert validate_result["checked"] == 1

    index_result = _run(["index", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert index_result["count"] == 1

    readme = (repo / "docs" / "decisions" / "README.md").read_text(encoding="utf-8")
    assert "ADR-0001" in readme
    assert "Accepted" in readme

    second_preflight = _run(["preflight", "--json"], cwd=repo)
    assert second_preflight["existing_adr_directory"] == "docs/decisions"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/integration/test_init_workflow.py -v`
Expected: FAIL — fixture doesn't exist yet (it's created in Step 1 above alongside the test; if you're following strict step order, running before creating `package.json` fails with a "fixture not found" style error since `discover` finds nothing).

- [ ] **Step 3: Nothing further to implement**

This task's "implementation" is the fixture file itself, created in Step 1. No production code changes — this task proves Tasks 1–16 already compose correctly end to end.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/integration/test_init_workflow.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/init_no_adr_js_project/package.json tests/integration/test_init_workflow.py
git commit -m "test: add end-to-end INIT fixture and golden test"
```

---

### Task 18: Generic harness fallback adapter

**Files:**
- Create: `adapters/generic/README.md`
- Test: `tests/unit/test_generic_adapter.py`

**Interfaces:**
- Consumes: nothing (documentation only).
- Produces: a manual-install path that works for any harness not covered by Task 16's Claude adapter — including harnesses that don't have a plugin/skill manifest system at all, as long as they read project instructions and can run shell commands.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_generic_adapter.py
from pathlib import Path

GENERIC_README = Path(__file__).resolve().parent.parent.parent / "adapters" / "generic" / "README.md"


def test_generic_adapter_readme_exists_and_documents_symlink_install():
    text = GENERIC_README.read_text(encoding="utf-8")
    assert "skills/adr-toolkit" in text
    assert "AGENTS.md" in text
    assert "SKILL.md" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_generic_adapter.py -v`
Expected: FAIL — file doesn't exist.

- [ ] **Step 3: Write the fallback guide**

```markdown
<!-- adapters/generic/README.md -->
# Generic harness adapter

If your AI coding harness isn't Claude Code, Codex, Gemini CLI, or
Antigravity CLI, ADR Toolkit still works — `SKILL.md` only assumes your
harness can read project instructions and run shell commands, which
covers effectively every current coding agent, including ones this
project hasn't been tested against yet.

## Install

1. Copy or symlink `skills/adr-toolkit/` into your project, at whatever
   path your harness scans for instructions or skills:

   ```bash
   mkdir -p .agents/skills
   ln -s ../../path/to/adr-toolkit/skills/adr-toolkit .agents/skills/adr-toolkit
   ```

2. Add one line to your project's `AGENTS.md` (or whatever instruction
   file your harness reads first):

   ```markdown
   For architecture decisions (introducing, recording, or checking ADRs),
   follow `.agents/skills/adr-toolkit/SKILL.md`.
   ```

3. That's it. `SKILL.md` never assumes a plugin manifest, a hook, or any
   harness-specific configuration — only that something can read markdown
   and run `python scripts/adr.py ...`.

## No agent at all?

You don't need one. Every deterministic operation is a plain CLI command
you can run yourself: `python skills/adr-toolkit/scripts/adr.py init`,
`... validate`, `... index`, and `... create --interactive` (see Task 19)
for a guided prompt sequence that needs no AI harness whatsoever.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_generic_adapter.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add adapters/generic/README.md tests/unit/test_generic_adapter.py
git commit -m "docs: add generic harness fallback adapter"
```

---

### Task 19: `create.py --interactive` — terminal wizard for humans with no agent

**Files:**
- Modify: `skills/adr-toolkit/scripts/commands/create.py` (Task 11)
- Modify: `skills/adr-toolkit/scripts/adr.py` (Task 14) — `--input` becomes optional, `--interactive` added
- Test: `tests/unit/test_create_interactive.py`

**Interfaces:**
- Consumes: nothing beyond what Task 11 already consumes.
- Produces: `gather_draft_interactively(input_fn=input) -> dict` (same draft shape Task 11's `run()` already expects: `title`, `status`, `body`). `run(args)` now accepts an `args.interactive` flag as an alternative to `args.input` — everything downstream (ID assignment, schema validation, file write) is unchanged.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_create_interactive.py
from types import SimpleNamespace

from scripts.commands import create


def test_gather_draft_interactively_builds_valid_minimal_body():
    answers = iter([
        "Use Kafka for domain events",
        "Order processing and downstream work are tightly coupled",
        "synchronous HTTP, RabbitMQ, Kafka",
        "Kafka",
        "it isolates failures and allows reprocessing",
        "failures in one consumer don't block others",
        "operational complexity increases",
        "no direct SDK calls appear outside the events module",
        "message volume exceeds what a single queue can handle",
    ])
    draft = create.gather_draft_interactively(input_fn=lambda _prompt: next(answers))

    assert draft["title"] == "Use Kafka for domain events"
    assert draft["status"] == "proposed"
    assert "## Context and Problem Statement" in draft["body"]
    assert "Kafka" in draft["body"]


def test_create_run_supports_interactive_mode_end_to_end(tmp_path, monkeypatch):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)

    answers = iter([
        "Use Kafka for domain events", "Problem text", "HTTP, Kafka", "Kafka",
        "reason", "good thing", "bad thing", "verification note", "revisit condition",
    ])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    result = create.run(SimpleNamespace(interactive=True, input=None, dir=str(adr_dir), dry_run=False))

    assert result["ok"] is True
    assert result["id"] == "ADR-0001"


def test_create_run_without_input_or_interactive_is_an_error(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)

    result = create.run(SimpleNamespace(interactive=False, input=None, dir=str(adr_dir), dry_run=False))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "MISSING_INPUT_OR_INTERACTIVE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_create_interactive.py -v`
Expected: FAIL — `gather_draft_interactively` doesn't exist; `run()` doesn't accept `interactive`/`None` input.

- [ ] **Step 3: Modify `create.py`**

Add this function anywhere above `run`:

```python
def _prompt(input_fn, question: str) -> str:
    return input_fn(f"{question}\n> ").strip()


def gather_draft_interactively(input_fn=input) -> dict:
    title = _prompt(input_fn, "Title of the decision?")
    problem = _prompt(input_fn, "What problem or constraint made this decision necessary?")
    options_raw = _prompt(input_fn, "Options considered (comma-separated)?")
    options = [o.strip() for o in options_raw.split(",") if o.strip()]
    decision = _prompt(input_fn, "Which option was chosen?")
    rationale = _prompt(input_fn, "Why was it chosen?")
    good = _prompt(input_fn, "One good consequence?")
    bad = _prompt(input_fn, "One accepted downside?")
    confirmation = _prompt(input_fn, "How will this be verified in the code?")
    revisit = _prompt(input_fn, "What condition should reopen this decision?")

    options_block = "\n".join(f"* {o}" for o in options) if options else f"* {decision}"

    body = (
        f"# {title}\n\n"
        "## Context and Problem Statement\n\n"
        f"{problem}\n\n"
        "## Considered Options\n\n"
        f"{options_block}\n\n"
        "## Decision Outcome\n\n"
        f"Chosen option: **{decision}**, because {rationale}.\n\n"
        "## Consequences\n\n"
        f"* Good: {good}\n"
        f"* Bad: {bad}\n\n"
        "## Confirmation\n\n"
        f"{confirmation}\n\n"
        "## Revisit Triggers\n\n"
        f"* {revisit}\n"
    )

    return {"title": title, "status": "proposed", "body": body}
```

Replace the start of `run(args)` (everything up to `adr_dir.mkdir`) with:

```python
def run(args) -> dict:
    dry_run = getattr(args, "dry_run", False)

    if getattr(args, "interactive", False):
        draft = gather_draft_interactively()
    else:
        input_path = getattr(args, "input", None)
        if not input_path:
            return {
                "ok": False,
                "operation": "create",
                "errors": [{"code": "MISSING_INPUT_OR_INTERACTIVE"}],
            }
        draft = json.loads(Path(input_path).read_text(encoding="utf-8"))

    adr_dir = Path(args.dir)
    missing = REQUIRED_DRAFT_FIELDS - draft.keys()
    if missing:
        return {
            "ok": False,
            "operation": "create",
            "errors": [{"code": "MISSING_DRAFT_FIELD", "fields": sorted(missing)}],
        }
```

(the rest of `run` — ID assignment, schema validation, file write — is unchanged from Task 11)

- [ ] **Step 4: Modify `adr.py`'s `create` subparser**

In `build_parser()`, replace:

```python
    p_create.add_argument("--input", required=True)
```

with:

```python
    p_create.add_argument("--input")
    p_create.add_argument("--interactive", action="store_true")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_create.py tests/unit/test_create_interactive.py -v`
Expected: PASS (7 tests total — Task 11's 4 plus this task's 3). Task 11's tests must still pass unchanged, since `getattr(args, "interactive", False)` defaults to `False` for their `SimpleNamespace` instances.

- [ ] **Step 6: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/create.py skills/adr-toolkit/scripts/adr.py \
        tests/unit/test_create_interactive.py
git commit -m "feat: add interactive create wizard for use without an AI agent"
```

---

### Task 20: CI workflow

**Files:**
- Create: `.github/workflows/test.yml`

**Interfaces:**
- Consumes: nothing new — runs the full test suite built by Tasks 1–19.
- Produces: CI enforcement on every push and PR.

- [ ] **Step 1: Write the workflow file**

```yaml
# .github/workflows/test.yml
name: test

on:
  push:
  pull_request:

jobs:
  pytest:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.9", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Run tests
        run: python -m pytest tests/unit tests/integration -v
```

- [ ] **Step 2: Run the equivalent command locally to confirm it would pass in CI**

Run: `python -m pytest tests/unit tests/integration -v`
Expected: PASS (every test added in Tasks 1–19)

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "ci: run pytest across unit and integration tests on every push and PR"
```

---

## Revision notes

**Revision 1** — After this plan was first written, the user reviewed a
separate improvement proposal and asked to fold in several low-cost
refinements before execution began (no code had been written yet).
Applied: INIT and DISCOVER split into two SKILL.md operations instead of
one bundled flow (Task 15), retrospective ADRs now require a Confirmed
Evidence/Inferred Rationale/Unknown structure (Task 15), and a "what
belongs in an ADR" classification table was added (Task 15, and spec §6.1).
No script-level tasks changed — `discover.py` (Task 8) already existed as
its own command, so this was purely a SKILL.md/documentation restructuring.
Structured `constraints:` YAML blocks and CHECK's four-way finding
classification were accepted too, but recorded only in the design spec
(§6.1, §7) since CHECK isn't implemented until Plan 3.

**Revision 2** — The user asked whether the design was actually natural to
use both for AI harnesses and for plain human developers. Two real gaps
surfaced: (1) the Codex/Gemini CLI/Antigravity adapter manifests planned
for Plan 4 rest on assumed, unverified schemas, and the original PRD's
harness-agnostic "Generic Agent Skills" fallback had been dropped when the
harness list was narrowed to four named ones; (2) `create.py` only accepted
a pre-built JSON draft, which is natural for an agent but not for a human
running the CLI directly with no AI harness at all — undermining the
stated goal of easy adoption by other developers. Added Task 18 (a
zero-maintenance generic fallback adapter — symlink + one `AGENTS.md` line
— that works for any harness, including ones not yet accounted for) and
Task 19 (`create --interactive`, a terminal wizard that needs no agent).
Both are documentation/CLI-only changes with no effect on Tasks 1–17.

## Plan self-review notes

- **Spec coverage:** §5 (repo structure) → Tasks 1, 16; §6 (ADR document format) → Tasks 2, 5, 9, 10, 11; §6.1 (what belongs in an ADR) → Task 15; §10 (multi-view index) → Task 12; §11 INIT/DISCOVER data flow → Tasks 6, 8, 10, 11, 13, 14, 15; §12 CI → Task 20; §8 Claude Code depth → Tasks 16, 17. Harness-naturalness and human-usability (raised in review, not in the original spec numbering) → Tasks 18 (generic adapter) and 19 (interactive wizard). RECORD (§11), CHECK (§7, §11), i18n (§9), and the Codex/Gemini CLI/Antigravity adapters (§8) are explicitly out of scope for this plan — see Plans 2–4.
- **Type consistency checked:** `identifiers.next_id`/`format_filename`/`slugify`/`parse_filename` signatures match across Tasks 3, 10, 11, 12, 13. `frontmatter.parse`/`serialize` signatures match across Tasks 2, 11, 12, 13, 15. `schema.validate_frontmatter` signature matches across Tasks 5, 11, 13.
- **No placeholders found** — every step has runnable code or literal file content; nothing deferred with "TODO" inside this plan's own tasks.

## Open item for the user

The design spec this plan implements (`docs/superpowers/specs/2026-08-29-adr-toolkit-design.md`) has not yet had a line-by-line review from the project owner — they approved the direction conversationally and asked me to keep moving while away. Two things in the spec worth their explicit attention when they're back, before this plan is executed:

1. §13 of the spec proposes MIT as the license — decided in their absence, needs confirmation before any public release.
2. §7's conflict-detection scope (structural/path evidence only, semantic taxonomy deferred) — discussed and agreed to, but worth a final look now that the concrete rule table exists.
