# ADR Toolkit — RECORD + Lifecycle (Plan 2 of 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the RECORD workflow (significance scoring, related-ADR search, forward-looking and retrospective-in-branch decision capture) and lifecycle operations (`status`, `supersede`, `deprecate`) on top of Plan 1's deterministic core.

**Architecture:** Two new deterministic layers — `scripts/rules/significance.py` (pure arithmetic classification the agent feeds its own per-criterion judgments into) and three new `scripts/commands/*.py` modules (`related`, `significance`, `status`, `supersede`) plus a `deprecate` subcommand that is a thin alias over `status`. `SKILL.md` gains RECORD and Lifecycle sections describing how the agent orchestrates these scripts; no new agent-side judgment logic is hardcoded in Python.

**Tech Stack:** Same as Plan 1 — Python 3.9+ standard library only, pytest.

**Spec:** `docs/superpowers/specs/2026-08-29-adr-toolkit-design.md` (§6.1, §11 RECORD, §11 Lifecycle operations)

## Global Constraints

- Same as Plan 1: Python 3.9+ stdlib only; UTF-8 explicit; no `shell=True`; mutating commands (`status`, `supersede`) support `--dry-run` and never silently overwrite; command modules never `print()`; avoid `X | None` union syntax, use `typing.Optional`.
- `status`/`supersede`/`deprecate` write ADR frontmatter only through `core.frontmatter.serialize` + `core.lifecycle.validate_transition` — never hand-format YAML, never skip the transition check.
- `deprecate <id>` is not a new command module — it is an `adr.py` subparser that calls `commands.status.run` with `to="deprecated"` pre-set via `set_defaults`, avoiding duplicated logic.
- Out of scope for this plan (tracked in `project-roadmap.md` / Plan 3/4): CHECK workflow, i18n wiring, Codex/Gemini CLI/Antigravity CLI adapters, release automation.
- Every task must leave `python -m pytest tests/unit tests/integration -v` green before its commit step.

---

### Task 1: `core/identifiers.find_by_number` — locate an ADR file by its numeric ID

**Files:**
- Modify: `skills/adr-toolkit/scripts/core/identifiers.py`
- Test: `tests/unit/test_identifiers.py` (add cases)

**Interfaces:**
- Consumes: nothing new.
- Produces: `find_by_number(adr_dir: Path, number: int) -> Optional[Path]`. Used by Tasks 6 (status) and 7 (supersede).

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_identifiers.py`:

```python
def test_find_by_number_locates_matching_file(tmp_path):
    (tmp_path / "0003-use-kafka.md").write_text("x", encoding="utf-8")
    found = identifiers.find_by_number(tmp_path, 3)
    assert found is not None
    assert found.name == "0003-use-kafka.md"


def test_find_by_number_returns_none_when_missing(tmp_path):
    assert identifiers.find_by_number(tmp_path, 7) is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_identifiers.py -v`
Expected: FAIL — `find_by_number` doesn't exist.

- [ ] **Step 3: Add the function**

Append to `skills/adr-toolkit/scripts/core/identifiers.py`:

```python
def find_by_number(adr_dir: Path, number: int) -> Optional[Path]:
    for entry in adr_dir.glob(f"{number:04d}-*.md"):
        return entry
    return None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_identifiers.py -v`
Expected: PASS (8 tests — 6 from Plan 1 plus these 2)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/core/identifiers.py tests/unit/test_identifiers.py
git commit -m "feat: add find_by_number for looking up an ADR by its ID"
```

---

### Task 2: `rules/significance.py` — deterministic significance classification

**Files:**
- Create: `skills/adr-toolkit/scripts/rules/__init__.py` (empty)
- Create: `skills/adr-toolkit/scripts/rules/significance.py`
- Test: `tests/unit/test_significance.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `CRITERIA: tuple`, `score(criteria_scores: dict) -> int`, `classify(total: int) -> str`. Used by Task 3 (`commands/significance.py`).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_significance.py
import pytest

from scripts.rules import significance

FULL_SCORES = {c: 2 for c in significance.CRITERIA}
ZERO_SCORES = {c: 0 for c in significance.CRITERIA}


def test_score_sums_all_seven_criteria():
    assert significance.score(FULL_SCORES) == 14
    assert significance.score(ZERO_SCORES) == 0


def test_score_defaults_missing_criteria_to_zero():
    assert significance.score({}) == 0


def test_score_rejects_out_of_range_value():
    with pytest.raises(ValueError):
        significance.score({"reversal_cost": 3})


def test_classify_bands():
    assert significance.classify(0) == "not_needed"
    assert significance.classify(3) == "not_needed"
    assert significance.classify(4) == "optional"
    assert significance.classify(6) == "optional"
    assert significance.classify(7) == "recommended"
    assert significance.classify(14) == "recommended"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_significance.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/rules/significance.py
"""Deterministic significance classification for RECORD.

The agent scores each of the 7 criteria itself (0, 1, or 2) based on its own
reading of the code and conversation — that judgment is not scriptable. This
module only sums and bands the result deterministically, so the same 7
scores always produce the same recommendation.
"""

CRITERIA = (
    "reversal_cost",
    "alternatives_considered",
    "quality_attribute_impact",
    "boundary_or_pattern_change",
    "multi_developer_relevance",
    "ops_security_data_impact",
    "future_rationale_query_likelihood",
)


def score(criteria_scores: dict) -> int:
    total = 0
    for criterion in CRITERIA:
        value = criteria_scores.get(criterion, 0)
        if value not in (0, 1, 2):
            raise ValueError(f"{criterion} must be 0, 1, or 2, got {value!r}")
        total += value
    return total


def classify(total: int) -> str:
    if total <= 3:
        return "not_needed"
    if total <= 6:
        return "optional"
    return "recommended"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_significance.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/rules tests/unit/test_significance.py
git commit -m "feat: add deterministic significance scoring/classification"
```

---

### Task 3: `commands/significance.py` — CLI wrapper + wire into `adr.py`

**Files:**
- Create: `skills/adr-toolkit/scripts/commands/significance.py`
- Modify: `skills/adr-toolkit/scripts/adr.py`
- Test: `tests/unit/test_significance_command.py`, `tests/integration/test_cli.py` (add one case)

**Interfaces:**
- Consumes: `scripts.rules.significance.{score, classify}` (Task 2).
- Produces: `run(args) -> dict` where `args.input` is a path to a JSON file of per-criterion scores. Used by `SKILL.md`'s RECORD flow (Task 10) and the CLI.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_significance_command.py
import json
from types import SimpleNamespace

from scripts.commands import significance


def test_significance_command_returns_total_and_classification(tmp_path):
    input_path = tmp_path / "scores.json"
    input_path.write_text(json.dumps({"reversal_cost": 2, "boundary_or_pattern_change": 2}), encoding="utf-8")

    result = significance.run(SimpleNamespace(input=str(input_path)))

    assert result["ok"] is True
    assert result["total"] == 4
    assert result["classification"] == "optional"


def test_significance_command_rejects_bad_score(tmp_path):
    input_path = tmp_path / "scores.json"
    input_path.write_text(json.dumps({"reversal_cost": 9}), encoding="utf-8")

    result = significance.run(SimpleNamespace(input=str(input_path)))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "INVALID_SCORE"
```

Append to `tests/integration/test_cli.py`:

```python
def test_significance_via_cli(tmp_path):
    scores_path = tmp_path / "scores.json"
    scores_path.write_text('{"reversal_cost": 2, "quality_attribute_impact": 2}', encoding="utf-8")
    result = _run(["significance", "--input", str(scores_path), "--json"], cwd=tmp_path)
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["total"] == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_significance_command.py tests/integration/test_cli.py -v`
Expected: FAIL — `commands.significance` and the `significance` subcommand don't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/commands/significance.py
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
```

In `skills/adr-toolkit/scripts/adr.py`, add the import and subparser:

```python
from scripts.commands import significance  # add alongside existing command imports
```

```python
    p_significance = sub.add_parser("significance")
    p_significance.add_argument("--input", required=True)
    p_significance.add_argument("--json", action="store_true")
```

Add `"significance": significance.run` to the `HANDLERS` dict.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_significance_command.py tests/integration/test_cli.py -v`
Expected: PASS (2 new unit tests, 1 new integration test, all prior tests still green)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/significance.py skills/adr-toolkit/scripts/adr.py \
        tests/unit/test_significance_command.py tests/integration/test_cli.py
git commit -m "feat: expose significance scoring as a CLI subcommand"
```

---

### Task 4: `commands/related.py` — related-ADR search + wire into `adr.py`

**Files:**
- Create: `skills/adr-toolkit/scripts/commands/related.py`
- Modify: `skills/adr-toolkit/scripts/adr.py`
- Test: `tests/unit/test_related.py`

**Interfaces:**
- Consumes: `scripts.core.frontmatter.parse` (Plan 1 Task 2), `scripts.core.identifiers.parse_filename` (Plan 1 Task 3).
- Produces: `run(args) -> dict` where `args` has optional `.paths` (list), `.tags` (list), `.keyword` (str), and `.dir`. Used by `SKILL.md`'s RECORD flow (Task 10).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_related.py
from types import SimpleNamespace

from scripts.commands import related

ADR_WITH_PATH = (
    "---\n"
    "id: ADR-0001\n"
    "title: Use Kafka for domain events\n"
    "status: accepted\n"
    "date: 2026-08-01\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths:\n"
    "  - src/events/\n"
    "tags:\n"
    "  - architecture\n"
    "retrospective: false\n"
    "---\n\n"
    "# Use Kafka for domain events\n"
)

ADR_UNRELATED = ADR_WITH_PATH.replace("0001", "0002").replace(
    "Use Kafka for domain events", "Use Postgres"
).replace("src/events/", "src/db/").replace("architecture", "data")


def test_finds_match_by_affected_path(tmp_path):
    (tmp_path / "0001-use-kafka.md").write_text(ADR_WITH_PATH, encoding="utf-8")
    (tmp_path / "0002-use-postgres.md").write_text(ADR_UNRELATED, encoding="utf-8")

    result = related.run(SimpleNamespace(dir=str(tmp_path), paths=["src/events/"], tags=None, keyword=None))

    assert result["ok"] is True
    assert result["count"] == 1
    assert result["matches"][0]["id"] == "ADR-0001"
    assert "affected_paths overlap" in result["matches"][0]["reasons"][0]


def test_finds_match_by_tag(tmp_path):
    (tmp_path / "0002-use-postgres.md").write_text(ADR_UNRELATED, encoding="utf-8")

    result = related.run(SimpleNamespace(dir=str(tmp_path), paths=None, tags=["data"], keyword=None))

    assert result["count"] == 1
    assert result["matches"][0]["id"] == "ADR-0002"


def test_no_match_returns_empty_list(tmp_path):
    (tmp_path / "0001-use-kafka.md").write_text(ADR_WITH_PATH, encoding="utf-8")

    result = related.run(SimpleNamespace(dir=str(tmp_path), paths=["src/unrelated/"], tags=None, keyword=None))

    assert result["count"] == 0
    assert result["matches"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_related.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/commands/related.py
"""Find existing ADRs related to a set of paths, tags, or a keyword."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers

SKIP_FILES = {"README.md", "adr-template.md"}


def run(args) -> dict:
    adr_dir = Path(args.dir)
    query_paths = set(getattr(args, "paths", None) or [])
    query_tags = set(getattr(args, "tags", None) or [])
    keyword = (getattr(args, "keyword", None) or "").lower()

    matches = []
    for entry in sorted(adr_dir.glob("*.md")):
        if entry.name in SKIP_FILES or identifiers.parse_filename(entry.name) is None:
            continue

        data, _ = fm.parse(entry.read_text(encoding="utf-8"))
        reasons = []

        path_overlap = query_paths & set(data.get("affected_paths", []))
        if path_overlap:
            reasons.append(f"affected_paths overlap: {sorted(path_overlap)}")

        tag_overlap = query_tags & set(data.get("tags", []))
        if tag_overlap:
            reasons.append(f"tag overlap: {sorted(tag_overlap)}")

        if keyword and keyword in data.get("title", "").lower():
            reasons.append("title keyword match")

        if reasons:
            matches.append({
                "id": data.get("id"),
                "filename": entry.name,
                "title": data.get("title"),
                "status": data.get("status"),
                "reasons": reasons,
            })

    return {"ok": True, "operation": "related", "count": len(matches), "matches": matches}
```

In `scripts/adr.py`, add:

```python
from scripts.commands import related  # alongside other imports
```

```python
    p_related = sub.add_parser("related")
    p_related.add_argument("--paths", nargs="*")
    p_related.add_argument("--tags", nargs="*")
    p_related.add_argument("--keyword")
    p_related.add_argument("--dir", default="docs/decisions")
    p_related.add_argument("--json", action="store_true")
```

Add `"related": related.run` to `HANDLERS`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_related.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/related.py skills/adr-toolkit/scripts/adr.py \
        tests/unit/test_related.py
git commit -m "feat: add related-ADR search by path/tag/keyword"
```

---

### Task 5: extend `core/schema.py` with optional `supersedes`/`superseded_by`

**Files:**
- Modify: `skills/adr-toolkit/scripts/core/schema.py`
- Test: `tests/unit/test_schema.py` (add cases)

**Interfaces:**
- Consumes: nothing new.
- Produces: `validate_frontmatter` now also accepts (but does not require) `supersedes: list` and `superseded_by: str`. Used by Task 7 (`commands/supersede.py`).

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_schema.py`:

```python
def test_optional_supersedes_field_is_allowed_when_a_list():
    data = dict(VALID, supersedes=["ADR-0002"])
    assert validate_frontmatter(data) == []


def test_optional_supersedes_field_wrong_type_is_reported():
    data = dict(VALID, supersedes="ADR-0002")  # should be a list
    errors = validate_frontmatter(data)
    assert any("supersedes" in e for e in errors)


def test_optional_superseded_by_field_is_allowed_when_a_string():
    data = dict(VALID, superseded_by="ADR-0009")
    assert validate_frontmatter(data) == []


def test_absence_of_optional_fields_is_not_an_error():
    assert validate_frontmatter(VALID) == []  # VALID has neither field, must still pass
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_schema.py -v`
Expected: FAIL on the wrong-type case (currently silently ignored since the field isn't in `REQUIRED_FIELDS` at all — the "wrong type is reported" test is the one that actually fails; the others already pass by accident, which is the point of this task: make the check explicit rather than absent).

- [ ] **Step 3: Extend the implementation**

In `skills/adr-toolkit/scripts/core/schema.py`, add alongside `REQUIRED_FIELDS`:

```python
OPTIONAL_FIELDS = {
    "supersedes": list,
    "superseded_by": str,
}
```

In `validate_frontmatter`, after the `REQUIRED_FIELDS` loop, add:

```python
    for field, expected_type in OPTIONAL_FIELDS.items():
        if field in data and not isinstance(data[field], expected_type):
            errors.append(
                f"field {field!r} must be {expected_type.__name__}, "
                f"got {type(data[field]).__name__}"
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_schema.py -v`
Expected: PASS (10 tests — 6 from Plan 1 plus these 4)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/core/schema.py tests/unit/test_schema.py
git commit -m "feat: validate optional supersedes/superseded_by fields"
```

---

### Task 6: `commands/status.py` — validated status transition, plus `deprecate` alias

**Files:**
- Create: `skills/adr-toolkit/scripts/commands/status.py`
- Modify: `skills/adr-toolkit/scripts/adr.py`
- Test: `tests/unit/test_status.py`

**Interfaces:**
- Consumes: `scripts.core.identifiers.find_by_number` (Task 1), `scripts.core.frontmatter.{parse, serialize}` (Plan 1 Task 2), `scripts.core.lifecycle.{validate_transition, InvalidTransitionError}` (Plan 1 Task 4).
- Produces: `run(args) -> dict` where `args` has `.adr_number` (int), `.to` (str), `.dir`, optional `.dry_run`. Used by Task 7 (`supersede.py` reuses the same transition-checking pattern, not this module directly) and by `adr.py`'s `deprecate` subcommand (same function, `to="deprecated"` preset).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_status.py
from types import SimpleNamespace

from scripts.commands import status

ACCEPTED_ADR = (
    "---\n"
    "id: ADR-0001\n"
    "title: Use Kafka\n"
    "status: proposed\n"
    "date: 2026-08-01\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths: []\n"
    "tags: []\n"
    "retrospective: false\n"
    "---\n\n"
    "# Use Kafka\n"
)


def test_valid_transition_updates_status(tmp_path):
    (tmp_path / "0001-use-kafka.md").write_text(ACCEPTED_ADR, encoding="utf-8")

    result = status.run(SimpleNamespace(adr_number=1, to="accepted", dir=str(tmp_path), dry_run=False))

    assert result["ok"] is True
    updated = (tmp_path / "0001-use-kafka.md").read_text(encoding="utf-8")
    assert "status: accepted" in updated


def test_invalid_transition_is_rejected(tmp_path):
    (tmp_path / "0001-use-kafka.md").write_text(ACCEPTED_ADR, encoding="utf-8")

    result = status.run(SimpleNamespace(adr_number=1, to="superseded", dir=str(tmp_path), dry_run=False))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "INVALID_TRANSITION"


def test_missing_adr_is_reported(tmp_path):
    result = status.run(SimpleNamespace(adr_number=99, to="accepted", dir=str(tmp_path), dry_run=False))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "ADR_NOT_FOUND"


def test_dry_run_does_not_write(tmp_path):
    (tmp_path / "0001-use-kafka.md").write_text(ACCEPTED_ADR, encoding="utf-8")

    result = status.run(SimpleNamespace(adr_number=1, to="accepted", dir=str(tmp_path), dry_run=True))

    assert result["ok"] is True
    assert result["dry_run"] is True
    unchanged = (tmp_path / "0001-use-kafka.md").read_text(encoding="utf-8")
    assert "status: proposed" in unchanged
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_status.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/commands/status.py
"""Change an ADR's status through the deterministic lifecycle state machine."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.lifecycle import InvalidTransitionError, validate_transition


def run(args) -> dict:
    adr_dir = Path(args.dir)
    target_file = identifiers.find_by_number(adr_dir, args.adr_number)

    if target_file is None:
        return {
            "ok": False,
            "operation": "status",
            "errors": [{"code": "ADR_NOT_FOUND", "id": args.adr_number}],
        }

    data, body = fm.parse(target_file.read_text(encoding="utf-8"))

    try:
        validate_transition(data["status"], args.to)
    except InvalidTransitionError as exc:
        return {
            "ok": False,
            "operation": "status",
            "errors": [{"code": "INVALID_TRANSITION", "detail": str(exc)}],
        }

    if getattr(args, "dry_run", False):
        return {
            "ok": True,
            "operation": "status",
            "dry_run": True,
            "would_update": str(target_file),
            "to": args.to,
        }

    data["status"] = args.to
    target_file.write_text(fm.serialize(data, body.strip() + "\n"), encoding="utf-8")

    return {"ok": True, "operation": "status", "dry_run": False, "updated": str(target_file), "to": args.to}
```

In `scripts/adr.py`, add:

```python
from scripts.commands import status  # alongside other imports
```

```python
    p_status = sub.add_parser("status")
    p_status.add_argument("adr_number", type=int)
    p_status.add_argument("--to", required=True)
    p_status.add_argument("--dir", default="docs/decisions")
    p_status.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_status.add_argument("--json", action="store_true")

    p_deprecate = sub.add_parser("deprecate")
    p_deprecate.add_argument("adr_number", type=int)
    p_deprecate.add_argument("--dir", default="docs/decisions")
    p_deprecate.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_deprecate.add_argument("--json", action="store_true")
    p_deprecate.set_defaults(to="deprecated")
```

Add both `"status": status.run` and `"deprecate": status.run` to `HANDLERS`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_status.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/status.py skills/adr-toolkit/scripts/adr.py \
        tests/unit/test_status.py
git commit -m "feat: add status transition command with a deprecate alias"
```

---

### Task 7: `commands/supersede.py` — bidirectional supersede link

**Files:**
- Create: `skills/adr-toolkit/scripts/commands/supersede.py`
- Modify: `skills/adr-toolkit/scripts/adr.py`
- Test: `tests/unit/test_supersede.py`

**Interfaces:**
- Consumes: `scripts.core.identifiers.find_by_number` (Task 1), `scripts.core.frontmatter.{parse, serialize}` (Plan 1 Task 2), `scripts.core.lifecycle.{validate_transition, InvalidTransitionError}` (Plan 1 Task 4), the `supersedes`/`superseded_by` fields validated by Task 5.
- Produces: `run(args) -> dict` where `args` has `.adr_number` (the old ADR, int), `.by` (the new ADR, int), `.dir`, optional `.dry_run`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_supersede.py
from types import SimpleNamespace

from scripts.commands import supersede

OLD_ADR = (
    "---\n"
    "id: ADR-0001\n"
    "title: Use RabbitMQ\n"
    "status: accepted\n"
    "date: 2026-08-01\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths: []\n"
    "tags: []\n"
    "retrospective: false\n"
    "---\n\n"
    "# Use RabbitMQ\n"
)

NEW_ADR = (
    "---\n"
    "id: ADR-0002\n"
    "title: Use Kafka\n"
    "status: accepted\n"
    "date: 2026-08-15\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths: []\n"
    "tags: []\n"
    "retrospective: false\n"
    "---\n\n"
    "# Use Kafka\n"
)


def test_supersede_updates_both_files(tmp_path):
    (tmp_path / "0001-use-rabbitmq.md").write_text(OLD_ADR, encoding="utf-8")
    (tmp_path / "0002-use-kafka.md").write_text(NEW_ADR, encoding="utf-8")

    result = supersede.run(SimpleNamespace(adr_number=1, by=2, dir=str(tmp_path), dry_run=False))

    assert result["ok"] is True
    old_text = (tmp_path / "0001-use-rabbitmq.md").read_text(encoding="utf-8")
    new_text = (tmp_path / "0002-use-kafka.md").read_text(encoding="utf-8")
    assert "status: superseded" in old_text
    assert "superseded_by: ADR-0002" in old_text
    assert "ADR-0001" in new_text  # appears in the new ADR's supersedes list


def test_supersede_missing_old_adr_is_reported(tmp_path):
    (tmp_path / "0002-use-kafka.md").write_text(NEW_ADR, encoding="utf-8")

    result = supersede.run(SimpleNamespace(adr_number=1, by=2, dir=str(tmp_path), dry_run=False))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "ADR_NOT_FOUND"


def test_supersede_dry_run_writes_nothing(tmp_path):
    (tmp_path / "0001-use-rabbitmq.md").write_text(OLD_ADR, encoding="utf-8")
    (tmp_path / "0002-use-kafka.md").write_text(NEW_ADR, encoding="utf-8")

    result = supersede.run(SimpleNamespace(adr_number=1, by=2, dir=str(tmp_path), dry_run=True))

    assert result["dry_run"] is True
    unchanged = (tmp_path / "0001-use-rabbitmq.md").read_text(encoding="utf-8")
    assert "status: accepted" in unchanged
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_supersede.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/commands/supersede.py
"""Mark one ADR as superseded by another, updating both files' frontmatter."""
from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core import identifiers
from scripts.core.lifecycle import InvalidTransitionError, validate_transition


def run(args) -> dict:
    adr_dir = Path(args.dir)
    old_file = identifiers.find_by_number(adr_dir, args.adr_number)
    new_file = identifiers.find_by_number(adr_dir, args.by)

    if old_file is None:
        return {"ok": False, "operation": "supersede", "errors": [{"code": "ADR_NOT_FOUND", "id": args.adr_number}]}
    if new_file is None:
        return {"ok": False, "operation": "supersede", "errors": [{"code": "ADR_NOT_FOUND", "id": args.by}]}

    old_data, old_body = fm.parse(old_file.read_text(encoding="utf-8"))

    try:
        validate_transition(old_data["status"], "superseded")
    except InvalidTransitionError as exc:
        return {"ok": False, "operation": "supersede", "errors": [{"code": "INVALID_TRANSITION", "detail": str(exc)}]}

    if getattr(args, "dry_run", False):
        return {
            "ok": True,
            "operation": "supersede",
            "dry_run": True,
            "would_update": [str(old_file), str(new_file)],
        }

    new_data, new_body = fm.parse(new_file.read_text(encoding="utf-8"))

    old_data["status"] = "superseded"
    old_data["superseded_by"] = new_data["id"]
    old_file.write_text(fm.serialize(old_data, old_body.strip() + "\n"), encoding="utf-8")

    supersedes_list = new_data.get("supersedes", [])
    if old_data["id"] not in supersedes_list:
        supersedes_list.append(old_data["id"])
    new_data["supersedes"] = supersedes_list
    new_file.write_text(fm.serialize(new_data, new_body.strip() + "\n"), encoding="utf-8")

    return {
        "ok": True,
        "operation": "supersede",
        "dry_run": False,
        "old": old_data["id"],
        "new": new_data["id"],
    }
```

In `scripts/adr.py`, add:

```python
from scripts.commands import supersede  # alongside other imports
```

```python
    p_supersede = sub.add_parser("supersede")
    p_supersede.add_argument("adr_number", type=int)
    p_supersede.add_argument("--by", type=int, required=True)
    p_supersede.add_argument("--dir", default="docs/decisions")
    p_supersede.add_argument("--dry-run", dest="dry_run", action="store_true")
    p_supersede.add_argument("--json", action="store_true")
```

Add `"supersede": supersede.run` to `HANDLERS`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_supersede.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/supersede.py skills/adr-toolkit/scripts/adr.py \
        tests/unit/test_supersede.py
git commit -m "feat: add supersede command with bidirectional link update"
```

---

### Task 8: `references/significance-rules.md`

**Files:**
- Create: `skills/adr-toolkit/references/significance-rules.md`
- Test: `tests/unit/test_significance_reference.py`

**Interfaces:**
- Consumes: nothing (content only, read by the agent during RECORD).
- Produces: the human/agent-readable explanation of the 7 criteria `rules/significance.py` (Task 2) scores arithmetically.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_significance_reference.py
from pathlib import Path

REFERENCE = (
    Path(__file__).resolve().parent.parent.parent
    / "skills" / "adr-toolkit" / "references" / "significance-rules.md"
)


def test_reference_documents_all_seven_criteria():
    text = REFERENCE.read_text(encoding="utf-8")
    for criterion in [
        "reversal_cost", "alternatives_considered", "quality_attribute_impact",
        "boundary_or_pattern_change", "multi_developer_relevance",
        "ops_security_data_impact", "future_rationale_query_likelihood",
    ]:
        assert criterion in text


def test_reference_documents_the_three_bands():
    text = REFERENCE.read_text(encoding="utf-8")
    assert "not_needed" in text
    assert "optional" in text
    assert "recommended" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_significance_reference.py -v`
Expected: FAIL — file doesn't exist.

- [ ] **Step 3: Write the content**

```markdown
<!-- skills/adr-toolkit/references/significance-rules.md -->
# Significance Scoring Reference

RECORD scores a candidate decision against 7 criteria, each 0/1/2, then
calls `python scripts/adr.py significance --input scores.json --json` to
get a deterministic band. The agent decides each score; the script only
sums and bands them — same inputs always produce the same recommendation.

## The 7 criteria

- `reversal_cost` — how expensive would it be to undo this later?
- `alternatives_considered` — were there multiple realistic options, or
  effectively one obvious choice?
- `quality_attribute_impact` — does this meaningfully affect performance,
  reliability, security, or another quality attribute?
- `boundary_or_pattern_change` — does this change a system boundary or a
  pattern other code is expected to follow?
- `multi_developer_relevance` — will other developers (or agents) need to
  follow this going forward?
- `ops_security_data_impact` — does this affect operations, security, or
  data consistency?
- `future_rationale_query_likelihood` — is someone likely to ask "why did
  we do it this way" months from now?

Score each 0 (no), 1 (somewhat), or 2 (clearly yes) based on the actual
code and conversation — never guess a score to force a particular band.

## Bands

- 0–3: `not_needed` — recommend a commit message or code comment instead.
- 4–6: `optional` — mention the option to the user, let them decide.
- 7–14: `recommended` — proceed to drafting an ADR.

The score is a decision aid, not a verdict the user can't override — if a
user insists on recording something scored `not_needed`, defer to them
rather than refusing.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_significance_reference.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/references/significance-rules.md tests/unit/test_significance_reference.py
git commit -m "docs: add significance scoring reference"
```

---

### Task 9: `references/interview-guide.md`

**Files:**
- Create: `skills/adr-toolkit/references/interview-guide.md`
- Test: `tests/unit/test_interview_guide.py`

**Interfaces:**
- Consumes: nothing (content only).
- Produces: the question-asking policy RECORD (and DISCOVER) follow.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_interview_guide.py
from pathlib import Path

REFERENCE = (
    Path(__file__).resolve().parent.parent.parent
    / "skills" / "adr-toolkit" / "references" / "interview-guide.md"
)


def test_guide_states_the_three_question_cap():
    text = REFERENCE.read_text(encoding="utf-8")
    assert "3" in text and "question" in text.lower()


def test_guide_lists_things_not_to_ask():
    text = REFERENCE.read_text(encoding="utf-8")
    assert "## What not to ask" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_interview_guide.py -v`
Expected: FAIL — file doesn't exist.

- [ ] **Step 3: Write the content**

```markdown
<!-- skills/adr-toolkit/references/interview-guide.md -->
# Interview Guide

RECORD and DISCOVER ask at most 3 questions per round. Fewer is better —
never ask a question `discover`/`related`/the repository already answered.

## Priority order (ask the highest-priority unanswered question first)

1. What problem or constraint made this decision necessary?
2. What realistic alternatives were considered?
3. Why was this option chosen over the others — what was the primary driver?
4. What negative consequence was knowingly accepted?
5. What condition should cause this decision to be revisited?

## What not to ask

- A library name or version already visible in a dependency manifest —
  `discover`/`related` already reported it.
- A policy already stated in an existing ADR — cite it instead.
- A preference with no effect on the file that gets written (e.g. writing
  style opinions).
- Anything the user already stated in their own request.

## If the user's answer is ambiguous

Ask one focused follow-up rather than guessing — but that follow-up still
counts against the 3-question cap for the round.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_interview_guide.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/references/interview-guide.md tests/unit/test_interview_guide.py
git commit -m "docs: add interview question-asking guide"
```

---

### Task 10: `SKILL.md` — RECORD and Lifecycle sections

**Files:**
- Modify: `skills/adr-toolkit/SKILL.md`
- Test: `tests/unit/test_skill_manifest.py` (add cases)

**Interfaces:**
- Consumes: all commands built in Tasks 1–9, plus Plan 1's `create`/`validate`/`index`.
- Produces: the RECORD and Lifecycle operation contracts an agent follows.

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_skill_manifest.py`:

```python
def test_skill_md_documents_record_and_lifecycle():
    _, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    assert "## RECORD" in body
    assert "## Lifecycle operations" in body
    assert "significance" in body
    assert "adr.py supersede" in body
    assert "adr.py deprecate" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_skill_manifest.py -v`
Expected: FAIL — sections don't exist yet.

- [ ] **Step 3: Add the sections**

Insert into `skills/adr-toolkit/SKILL.md`, after the `## What belongs in an ADR` section and before `## Prohibited`:

```markdown
## RECORD

Use RECORD both before implementing something (a forward-looking question)
and after (e.g. "find what in this branch should become an ADR" — same
flow, the trigger is a diff/branch range instead of a question).

1. **PREFLIGHT** — confirm an ADR directory exists (`preflight --json`); if
   not, tell the user to run INIT first.
2. **GATHER EVIDENCE** — run
   `python scripts/adr.py related --paths <affected-paths> --tags <tags> --json`
   to find existing ADRs that might already cover this, or that this new
   decision might conflict with or supersede.
3. **CLASSIFY** — use the `## What belongs in an ADR` table. Score the
   candidate against the 7 criteria in `references/significance-rules.md`,
   write the scores to a JSON file, and run
   `python scripts/adr.py significance --input scores.json --json`.
   - `not_needed` → recommend a commit message or code comment instead;
     do not draft an ADR unless the user insists.
   - `optional` → mention the option, let the user decide.
   - `recommended` → continue.
4. **ASK-IF-NEEDED** — at most 3 questions, following
   `references/interview-guide.md`'s priority order. Skip anything
   `related`/`discover`/the user's own request already answered.
5. **PLAN** — draft a MADR body (minimal or full, per
   `references/madr-guide.md`). If this decision replaces an existing
   Accepted ADR, note which one — that becomes a `supersede` call after
   approval, not a manual edit.
6. **CONFIRM** — show title, problem, options, decision, primary driver,
   accepted downside, and affected paths before writing anything.
7. **MUTATE** — write the draft JSON and run
   `python scripts/adr.py create --input <draft.json> --dir docs/decisions`.
   If this decision supersedes an existing one, follow with
   `python scripts/adr.py supersede <old-number> --by <new-number>` only
   after the user confirms that's intended.
8. **VALIDATE** — `validate --json` then `index --json`.
9. **REPORT** — facts found, judgment (including the significance score),
   questions asked, files created/updated, validation result, remaining
   uncertainty.

## Lifecycle operations

Status changes are explicit, user-triggered, and always go through the
deterministic transition check — never hand-edit a `status:` field.

| User says | Run |
|---|---|
| "이 ADR을 승인 상태로 변경해줘" / "mark this ADR accepted" | `python scripts/adr.py status <N> --to accepted` |
| "ADR-0012는 ADR-0021로 대체됐어" / "this supersedes ADR-0012" | `python scripts/adr.py supersede 12 --by 21` |
| "이 결정은 더 이상 적용되지 않아" / "deprecate this ADR" | `python scripts/adr.py deprecate <N>` |

Show the user the change (old status → new status, or which two ADRs link)
before running the non-dry-run command. If the script returns
`INVALID_TRANSITION`, explain why (per `references/lifecycle.md`) rather
than retrying with a different status.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_skill_manifest.py -v`
Expected: PASS (all prior cases plus this one)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/SKILL.md tests/unit/test_skill_manifest.py
git commit -m "feat: document RECORD and Lifecycle operations in SKILL.md"
```

---

### Task 11: End-to-end RECORD fixture and golden test

**Files:**
- Create: `tests/fixtures/record_existing_adr/docs/decisions/0001-use-rabbitmq.md`
- Create: `tests/integration/test_record_workflow.py`

**Interfaces:**
- Consumes: `related`, `significance`, `create`, `validate`, `index` via subprocess (Tasks 3, 4, and Plan 1's `create`/`validate`/`index`).
- Produces: the golden proof that RECORD's scripted steps compose correctly against a repo with pre-existing ADRs.

- [ ] **Step 1: Write the failing test**

```markdown
<!-- tests/fixtures/record_existing_adr/docs/decisions/0001-use-rabbitmq.md -->
---
id: ADR-0001
title: Use RabbitMQ for async processing
status: accepted
date: 2026-07-01
decision_makers: []
related: []
affected_paths:
  - src/queue/
tags:
  - architecture
retrospective: false
---

# Use RabbitMQ for async processing

Body.
```

```python
# tests/integration/test_record_workflow.py
import json
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "record_existing_adr"
ADR_PY = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit" / "scripts" / "adr.py"


def _run(args, cwd):
    result = subprocess.run([sys.executable, str(ADR_PY), *args], cwd=cwd, capture_output=True, text=True)
    assert result.returncode in (0, 1), result.stderr
    return json.loads(result.stdout)


def test_record_finds_related_scores_and_creates_new_adr(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)

    related_result = _run(["related", "--tags", "architecture", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert related_result["count"] == 1
    assert related_result["matches"][0]["id"] == "ADR-0001"

    scores_path = repo / "scores.json"
    scores_path.write_text(json.dumps({
        "reversal_cost": 2, "boundary_or_pattern_change": 2,
        "multi_developer_relevance": 2, "ops_security_data_impact": 1,
    }), encoding="utf-8")
    sig_result = _run(["significance", "--input", "scores.json", "--json"], cwd=repo)
    assert sig_result["classification"] == "recommended"

    draft_path = repo / "draft.json"
    draft_path.write_text(json.dumps({
        "title": "Use Kafka instead of RabbitMQ",
        "status": "accepted",
        "body": "# Use Kafka instead of RabbitMQ\n\nBody.\n",
        "related": ["ADR-0001"],
    }), encoding="utf-8")
    create_result = _run(["create", "--input", "draft.json", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert create_result["id"] == "ADR-0002"

    validate_result = _run(["validate", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert validate_result["ok"] is True
    assert validate_result["checked"] == 2

    supersede_result = _run(["supersede", "1", "--by", "2", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert supersede_result["ok"] is True

    old_text = (repo / "docs" / "decisions" / "0001-use-rabbitmq.md").read_text(encoding="utf-8")
    assert "status: superseded" in old_text
    assert "superseded_by: ADR-0002" in old_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/integration/test_record_workflow.py -v`
Expected: FAIL — fixture doesn't exist until Step 1's file is created.

- [ ] **Step 3: Nothing further to implement**

This task's "implementation" is the fixture itself. No production code changes — it proves Tasks 1–10 already compose correctly end to end.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/integration/test_record_workflow.py -v`
Expected: PASS (1 test)

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/record_existing_adr tests/integration/test_record_workflow.py
git commit -m "test: add end-to-end RECORD/supersede fixture and golden test"
```

---

## Plan self-review notes

- **Spec coverage:** §11 RECORD → Tasks 2, 3, 4, 8, 9, 10, 11; §11 Lifecycle operations → Tasks 1, 5, 6, 7, 10; §6.1 (what belongs in an ADR, reused by RECORD) → Task 10 (references it, no new implementation needed — already built in Plan 1). CHECK, i18n, and the remaining harness adapters are explicitly out of scope — Plans 3 and 4.
- **Type consistency checked:** `identifiers.find_by_number` signature (Task 1) matches its use in Tasks 6 and 7. `schema.validate_frontmatter`'s new optional-field handling (Task 5) doesn't change its existing signature or break any Plan 1 caller. `status.run` is reused unmodified as the `deprecate` handler via `set_defaults(to="deprecated")`, not a second copy of the transition logic.
- **No placeholders found.**

## Execution status

- Completed on 2026-08-30 via subagent-driven-development: all 11 tasks were
  implemented and task-reviewed, including fix rounds for issues found during
  review. The resulting unit and integration suite has 105 passing tests.
- The remaining user decisions are the public-release license and whether the
  final MVP retains five languages and four named harnesses. Neither blocked
  Plan 2.
- Codex `quick_validate.py` compatibility with the existing cross-harness
  `user-invocable` and `version` skill frontmatter keys remains tracked in
  `improvements.md` as a metadata/validator compatibility risk.
