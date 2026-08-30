import subprocess
from types import SimpleNamespace

from scripts.commands import check, create
from scripts.core import frontmatter as fm

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


def test_unreadable_adr_file_degrades_to_warning_and_keeps_other_findings(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-use-a-provider-port.md").write_text(ACCEPTED_ADR_WITH_RULE, encoding="utf-8")
    (adr_dir / "0010-invalid-utf8.md").write_bytes(b"\xff\xfe not valid utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "src" / "features").mkdir(parents=True)
    (tmp_path / "src" / "features" / "x.py").write_text("import openai\n", encoding="utf-8")

    result = check.run(_args(tmp_path, adr_dir))

    assert result["ok"] is True
    violation = next(f for f in result["findings"] if f["kind"] == "verified_violation")
    assert violation["adr_id"] == "ADR-0001"
    assert any(w["code"] == "BAD_FRONTMATTER" and w["file"] == "0010-invalid-utf8.md" for w in result["warnings"])


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
    assert "src/events/replay.py" in finding["evidence"]["unrealized_paths"]


def test_review_required_when_confirmed_path_is_renamed(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs/decisions"
    adr_dir.mkdir(parents=True)
    adr = ACCEPTED_ADR_WITH_VERIFICATION.replace(
        "src/events/replay.py", "src/old.py"
    ).replace("src/events/", "src/old.py")
    (adr_dir / "0003-add-event-replay.md").write_text(adr, encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/old.py").write_text("def replay(): pass\n", encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)
    _git(["mv", "src/old.py", "src/new.py"], tmp_path)

    args = _args(tmp_path, adr_dir)
    args.staged = True
    args.uncommitted = False
    result = check.run(args)

    finding = next(f for f in result["findings"] if f["kind"] == "review_required")
    assert finding["adr_id"] == "ADR-0003"
    assert finding["evidence"]["unrealized_paths"] == ["src/old.py"]


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


# --- Regression tests for the final whole-branch review of Plan 3 (CHECK) ---


def _toolkit_authored_adr(*, adr_id, affected_path, confirmation) -> str:
    """Build an ADR body the way `create` actually builds one.

    Deliberately *not* a synthetic `## Verification` fixture: the toolkit's own
    interview writes `## Confirmation`, and a fixture that hardcoded
    `## Verification` is exactly what let the heuristic rot into dead code.
    """
    answers = iter([
        "Add event replay",              # title
        "Replays are needed for audit",  # problem
        "replay module, manual rerun",   # options
        "replay module",                 # decision
        "it is automatable",             # rationale
        "auditable history",             # good consequence
        "extra storage",                 # bad consequence
        confirmation,                    # "How will this be verified in the code?"
        "if storage cost dominates",     # revisit trigger
    ])
    draft = create.gather_draft_interactively(input_fn=lambda _: next(answers))
    assert "## Confirmation" in draft["body"]

    data = {
        "id": adr_id,
        "title": draft["title"],
        "status": "accepted",
        "date": "2026-08-03",
        "decision_makers": [],
        "related": [],
        "affected_paths": [affected_path],
        "tags": [],
        "retrospective": False,
    }
    return fm.serialize(data, draft["body"].strip() + "\n")


def test_review_required_fires_on_a_confirmation_section_written_by_create(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0003-add-event-replay.md").write_text(
        _toolkit_authored_adr(
            adr_id="ADR-0003",
            affected_path="src/events/",
            confirmation="`src/events/replay.py` implements the replay handler.",
        ),
        encoding="utf-8",
    )
    (tmp_path / "src" / "events").mkdir(parents=True)
    (tmp_path / "src" / "events" / "replay.py").write_text("def replay(): pass\n", encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "src" / "events" / "replay.py").unlink()

    result = check.run(_args(tmp_path, adr_dir))

    finding = next(f for f in result["findings"] if f["kind"] == "review_required")
    assert finding["adr_id"] == "ADR-0003"
    assert "src/events/replay.py" in finding["evidence"]["unrealized_paths"]


def test_review_required_fires_when_a_confirmation_path_was_never_created(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0003-add-event-replay.md").write_text(
        _toolkit_authored_adr(
            adr_id="ADR-0003",
            affected_path="src/events/",
            confirmation="`tests/test_replay.py` covers the replay handler.",
        ),
        encoding="utf-8",
    )
    (tmp_path / "src" / "events").mkdir(parents=True)
    (tmp_path / "src" / "events" / "handler.py").write_text("x = 1\n", encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    # Touch a governed path, but never create the test the Confirmation names.
    (tmp_path / "src" / "events" / "handler.py").write_text("x = 2\n", encoding="utf-8")

    result = check.run(_args(tmp_path, adr_dir))

    finding = next(f for f in result["findings"] if f["kind"] == "review_required")
    assert finding["adr_id"] == "ADR-0003"
    assert finding["evidence"]["unrealized_paths"] == ["tests/test_replay.py"]


def test_ignored_artifact_does_not_satisfy_file_must_exist(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs/decisions"
    adr_dir.mkdir(parents=True)
    adr = """---
id: ADR-0011
title: Require generated policy manifest
status: accepted
date: 2026-08-03
decision_makers: []
related: []
affected_paths:
  - src/
tags: []
retrospective: false
---

# Require generated policy manifest

## Implementation Constraints

```yaml
constraints:
  - id: generated-policy-must-be-versioned
    kind: file_must_exist
    paths: ["build/generated-policy.json"]
    pattern: []
    severity: major
    message: "The generated policy manifest must be versioned."
```
"""
    (adr_dir / "0011-require-generated-policy-manifest.md").write_text(
        adr, encoding="utf-8"
    )
    (tmp_path / ".gitignore").write_text("build/\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/app.py").write_text("value = 1\n", encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "build").mkdir()
    (tmp_path / "build/generated-policy.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "src/app.py").write_text("value = 2\n", encoding="utf-8")

    result = check.run(_args(tmp_path, adr_dir))

    violation = next(f for f in result["findings"] if f["kind"] == "verified_violation")
    assert violation["rule_id"] == "generated-policy-must-be-versioned"
    assert violation["evidence"]["missing_paths"] == ["build/generated-policy.json"]


STRING_AFFECTED_PATHS_ADR = """---
id: ADR-0020
title: Scalar affected paths
status: accepted
date: 2026-08-04
decision_makers: []
related: []
affected_paths: src/features/
tags: []
retrospective: false
---

# Scalar affected paths

No constraints block here.
"""

BOOL_AFFECTED_PATHS_ADR = """---
id: ADR-0021
title: Boolean affected paths
status: superseded
superseded_by: ADR-0022
date: 2026-08-04
decision_makers: []
related: []
affected_paths: false
tags: []
retrospective: false
---

# Boolean affected paths

Superseded.
"""


def test_string_valued_affected_paths_does_not_match_character_by_character(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0020-scalar-affected-paths.md").write_text(STRING_AFFECTED_PATHS_ADR, encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    # "s" in "src/features/" would falsely match this path if the scalar string
    # were iterated character by character.
    (tmp_path / "setup.py").write_text("x = 1\n", encoding="utf-8")

    result = check.run(_args(tmp_path, adr_dir))

    assert result["ok"] is True
    assert result["findings"] == []


def test_bool_valued_affected_paths_does_not_abort_the_run(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0021-boolean-affected-paths.md").write_text(BOOL_AFFECTED_PATHS_ADR, encoding="utf-8")
    (adr_dir / "0001-use-a-provider-port.md").write_text(ACCEPTED_ADR_WITH_RULE, encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "src" / "features").mkdir(parents=True)
    (tmp_path / "src" / "features" / "x.py").write_text("import openai\n", encoding="utf-8")

    result = check.run(_args(tmp_path, adr_dir))

    assert result["ok"] is True
    violation = next(f for f in result["findings"] if f["kind"] == "verified_violation")
    assert violation["adr_id"] == "ADR-0001"


BAD_REGEX_ADR = """---
id: ADR-0030
title: Rule with a malformed regex
status: accepted
date: 2026-08-05
decision_makers: []
related: []
affected_paths:
  - src/features/
tags: []
retrospective: false
---

# Rule with a malformed regex

## Implementation Constraints

```yaml
constraints:
  - id: broken-pattern
    kind: forbidden_import
    paths: ["src/features/**"]
    pattern: ["("]
    severity: major
    message: "Unparseable pattern."
```
"""


def test_malformed_regex_pattern_degrades_to_a_warning(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0030-rule-with-a-malformed-regex.md").write_text(BAD_REGEX_ADR, encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "src" / "features").mkdir(parents=True)
    (tmp_path / "src" / "features" / "x.py").write_text("import openai\n", encoding="utf-8")

    result = check.run(_args(tmp_path, adr_dir))

    assert result["ok"] is True
    assert any(
        w["code"] == "BAD_CONSTRAINTS" and w.get("rule_id") == "broken-pattern"
        for w in result["warnings"]
    )


UNKNOWN_KIND_ADR = """---
id: ADR-0040
title: Rule with a typo kind
status: accepted
date: 2026-08-06
decision_makers: []
related: []
affected_paths:
  - src/features/
tags: []
retrospective: false
---

# Rule with a typo kind

## Implementation Constraints

```yaml
constraints:
  - id: typo-kind
    kind: forbidden_imports
    paths: ["src/features/**"]
    pattern: ["openai"]
    severity: major
    message: "Feature modules must use the LLM port."
```
"""


def test_unknown_constraint_kind_surfaces_as_a_warning_not_a_silent_related(tmp_path):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0040-rule-with-a-typo-kind.md").write_text(UNKNOWN_KIND_ADR, encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "src" / "features").mkdir(parents=True)
    (tmp_path / "src" / "features" / "x.py").write_text("import openai\n", encoding="utf-8")

    result = check.run(_args(tmp_path, adr_dir))

    assert result["ok"] is True
    assert any(
        w["code"] == "BAD_CONSTRAINTS" and w["adr_id"] == "ADR-0040"
        and "forbidden_imports" in w["detail"]
        for w in result["warnings"]
    )
    finding = next(f for f in result["findings"] if f["adr_id"] == "ADR-0040")
    assert finding["kind"] != "related"


def test_nonexistent_adr_directory_is_an_explicit_error(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "unrelated.py").write_text("x = 1\n", encoding="utf-8")

    result = check.run(SimpleNamespace(
        dir="does/not/exist", staged=False, uncommitted=True, since=None, root=str(tmp_path),
    ))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "ADR_DIR_NOT_FOUND"


def test_relative_dir_resolves_against_root_not_the_process_cwd(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-use-a-provider-port.md").write_text(ACCEPTED_ADR_WITH_RULE, encoding="utf-8")
    _git(["add", "-A"], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)

    (tmp_path / "src" / "features").mkdir(parents=True)
    (tmp_path / "src" / "features" / "x.py").write_text("import openai\n", encoding="utf-8")

    elsewhere = tmp_path.parent / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    result = check.run(SimpleNamespace(
        dir="docs/decisions", staged=False, uncommitted=True, since=None, root=str(tmp_path),
    ))

    assert result["ok"] is True
    violation = next(f for f in result["findings"] if f["kind"] == "verified_violation")
    assert violation["adr_id"] == "ADR-0001"
