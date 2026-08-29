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
