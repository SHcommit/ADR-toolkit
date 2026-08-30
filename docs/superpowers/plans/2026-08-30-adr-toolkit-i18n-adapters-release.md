# ADR Toolkit — i18n, Adapters, Release Automation (Plan 4 of 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close out the MVP — localize `index.py`'s generated `README.md` into 5 languages, add light adapters for Codex CLI, Gemini CLI, and Antigravity CLI (verified manifest formats, not guessed), and add version synchronization plus a tag-triggered release workflow.

**Architecture:** Three independent layers, matching the plan's three sections. i18n: a small `core/locale.py` loader (English-fallback merge) plus five flat `scripts/i18n/{locale}.json` files, consumed only by `index.py`'s `--locale` flag — no other module needs translation, since everything else is agent-composed prose. Adapters: three new `adapters/<harness>/` directories, each holding only a manifest file plus a README documenting a symlink-based install (mirroring `adapters/generic/README.md`) — no symlink is committed to the repo itself, since a real symlink checked into git breaks on Windows CI (`windows-latest` is in `test.yml`'s matrix) unless `core.symlinks` is enabled, which cannot be assumed. Release: a repo-root `scripts/sync_version.py` (tooling for the repo, not part of the distributable `skills/adr-toolkit/` package) plus a CI drift-check and a new tag-triggered `release.yml`.

**Tech Stack:** Same as Plans 1–3 — Python 3.9+ standard library only, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-29-adr-toolkit-design.md` (§17 Plan 4 implementation decisions — primary source; §8 harness support strategy; §9 internationalization scope)

## Global Constraints

- Same as Plans 1–3: Python 3.9+ stdlib only; UTF-8 explicit; no `shell=True`; command modules never `print()`; avoid `X | None` union syntax, use `typing.Optional`.
- i18n covers only `index.py`'s generated strings (§17.1) — never SKILL.md's own agent instructions, never RECORD/DISCOVER/CHECK's agent-composed questions/reports. A locale file or key that's missing falls back to English, never a crash and never a raw key name shown to a user.
- No adapter directory commits an actual symlink to git — every adapter's `skills/adr-toolkit` link is created at install time per that adapter's README, exactly like `adapters/generic/README.md` already documents. This avoids Windows CI (`test.yml`'s `windows-latest` matrix leg) breaking on an uncommitted-symlink-support assumption.
- `scripts/sync_version.py` lives at the repo root, not under `skills/adr-toolkit/` — it is tooling for this repository, not part of the distributable skill package.
- Manual end-to-end adapter verification (§17.2) only happens where a real harness CLI is present in this environment (`codex` 0.151.0, `gemini` 0.46.0 — confirmed installed). The Antigravity task is scoped to structural/schema verification only; its report must say so plainly, never claim an end-to-end run that didn't happen.
- Every task must leave `python -m pytest tests/unit tests/integration -v` green before its commit step.
- Out of scope for this plan: the CHECK follow-ups tracked in `project-roadmap.md`'s "CHECK follow-ups" section, and `adr.py`'s `--json`-always-emits-JSON standing risk (tracked in `handoff.md`, untouched here).

---

### Task 1: `core/locale.py` + the five locale JSON files

**Files:**
- Create: `skills/adr-toolkit/scripts/core/locale.py`
- Create: `skills/adr-toolkit/scripts/i18n/en.json`
- Create: `skills/adr-toolkit/scripts/i18n/fr.json`
- Create: `skills/adr-toolkit/scripts/i18n/ja.json`
- Create: `skills/adr-toolkit/scripts/i18n/ko.json`
- Create: `skills/adr-toolkit/scripts/i18n/zh.json`
- Test: `tests/unit/test_locale.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `load_locale(locale: str) -> dict`, `DEFAULT_LOCALE = "en"`. Used by Task 2 (`commands/index.py`).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_locale.py
from scripts.core.locale import DEFAULT_LOCALE, load_locale

REQUIRED_KEYS = {
    "decision_log_title", "by_status", "by_tag", "by_affected_path",
    "chronological", "status.proposed", "status.accepted",
    "status.rejected", "status.deprecated", "status.superseded",
}


def test_default_locale_is_english():
    assert DEFAULT_LOCALE == "en"


def test_english_locale_has_all_required_keys():
    strings = load_locale("en")
    assert REQUIRED_KEYS.issubset(strings.keys())


def test_every_shipped_locale_has_all_required_keys():
    for locale in ("en", "fr", "ja", "ko", "zh"):
        strings = load_locale(locale)
        missing = REQUIRED_KEYS - strings.keys()
        assert not missing, f"{locale} is missing keys: {missing}"


def test_french_translates_a_known_string():
    strings = load_locale("fr")
    assert strings["by_status"] == "Par statut"


def test_missing_locale_falls_back_to_english():
    strings = load_locale("xx")
    assert strings["by_status"] == "By status"


def test_missing_key_in_a_present_locale_falls_back_to_english(tmp_path, monkeypatch):
    import scripts.core.locale as locale_module
    partial_dir = tmp_path / "i18n"
    partial_dir.mkdir()
    (partial_dir / "en.json").write_text('{"by_status": "By status"}', encoding="utf-8")
    (partial_dir / "xx.json").write_text('{}', encoding="utf-8")
    monkeypatch.setattr(locale_module, "I18N_DIR", partial_dir)

    strings = locale_module.load_locale("xx")

    assert strings["by_status"] == "By status"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_locale.py -v`
Expected: FAIL — `scripts.core.locale` doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# skills/adr-toolkit/scripts/core/locale.py
"""Load i18n locale files for index.py's generated strings.

Every other user-facing string in this toolkit (RECORD/DISCOVER/CHECK's
interview questions and reports) is composed by the agent, not a fixed
Python string, so it needs no translation table — only index.py's
generated README.md content is a translation target (design spec §17.1).
"""
import json
from pathlib import Path

I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"
DEFAULT_LOCALE = "en"


def load_locale(locale: str) -> dict:
    base = _load_json(DEFAULT_LOCALE)
    if locale == DEFAULT_LOCALE:
        return base
    overlay = _load_json(locale)
    return {**base, **overlay}


def _load_json(locale: str) -> dict:
    path = I18N_DIR / f"{locale}.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
```

```json
// skills/adr-toolkit/scripts/i18n/en.json
{
  "decision_log_title": "Decision Log",
  "by_status": "By status",
  "by_tag": "By tag",
  "by_affected_path": "By affected path",
  "chronological": "Chronological (newest first)",
  "status.proposed": "Proposed",
  "status.accepted": "Accepted",
  "status.rejected": "Rejected",
  "status.deprecated": "Deprecated",
  "status.superseded": "Superseded"
}
```

```json
// skills/adr-toolkit/scripts/i18n/fr.json
{
  "decision_log_title": "Journal des décisions",
  "by_status": "Par statut",
  "by_tag": "Par étiquette",
  "by_affected_path": "Par chemin concerné",
  "chronological": "Chronologique (plus récent d'abord)",
  "status.proposed": "Proposé",
  "status.accepted": "Accepté",
  "status.rejected": "Rejeté",
  "status.deprecated": "Déprécié",
  "status.superseded": "Remplacé"
}
```

```json
// skills/adr-toolkit/scripts/i18n/ja.json
{
  "decision_log_title": "決定記録",
  "by_status": "ステータス別",
  "by_tag": "タグ別",
  "by_affected_path": "影響パス別",
  "chronological": "時系列（新しい順）",
  "status.proposed": "提案中",
  "status.accepted": "承認済み",
  "status.rejected": "却下",
  "status.deprecated": "非推奨",
  "status.superseded": "置き換え済み"
}
```

```json
// skills/adr-toolkit/scripts/i18n/ko.json
{
  "decision_log_title": "결정 기록",
  "by_status": "상태별",
  "by_tag": "태그별",
  "by_affected_path": "영향 경로별",
  "chronological": "시간순 (최신순)",
  "status.proposed": "제안됨",
  "status.accepted": "승인됨",
  "status.rejected": "거부됨",
  "status.deprecated": "폐기됨",
  "status.superseded": "대체됨"
}
```

```json
// skills/adr-toolkit/scripts/i18n/zh.json
{
  "decision_log_title": "决策日志",
  "by_status": "按状态",
  "by_tag": "按标签",
  "by_affected_path": "按受影响路径",
  "chronological": "按时间顺序（最新优先）",
  "status.proposed": "已提议",
  "status.accepted": "已接受",
  "status.rejected": "已拒绝",
  "status.deprecated": "已弃用",
  "status.superseded": "已取代"
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_locale.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/core/locale.py skills/adr-toolkit/scripts/i18n \
        tests/unit/test_locale.py
git commit -m "feat: add locale loader and five i18n string files"
```

---

### Task 2: `index.py --locale` — localized index generation

**Files:**
- Modify: `skills/adr-toolkit/scripts/commands/index.py`
- Modify: `skills/adr-toolkit/scripts/adr.py`
- Test: `tests/unit/test_index.py` (add cases)

**Interfaces:**
- Consumes: `scripts.core.locale.load_locale` (Task 1).
- Produces: `run(args) -> dict` where `args` gains an optional `.locale` attribute (default `"en"` when absent). `_render(entries, strings)` now takes the loaded locale dict as a second parameter. Used by Task 3 (`SKILL.md`, documentation only — no code dependency).

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_index.py`:

```python
def test_index_renders_french_headers_and_status_labels(tmp_path):
    _write_adr(
        tmp_path, "0001-use-kafka.md",
        id_="ADR-0001", title="Use Kafka", status="accepted", date="2026-08-01",
        tags=["architecture"], affected_paths=["src/events/"],
    )

    result = index.run(SimpleNamespace(dir=str(tmp_path), locale="fr"))

    assert result["ok"] is True
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "Journal des décisions" in readme
    assert "Par statut" in readme
    assert "Accepté" in readme
    assert "Par étiquette" in readme
    assert "Par chemin concerné" in readme
    assert "Chronologique (plus récent d'abord)" in readme


def test_index_defaults_to_english_when_locale_omitted(tmp_path):
    _write_adr(
        tmp_path, "0001-use-kafka.md",
        id_="ADR-0001", title="Use Kafka", status="accepted", date="2026-08-01",
        tags=["architecture"], affected_paths=["src/events/"],
    )

    result = index.run(SimpleNamespace(dir=str(tmp_path)))

    assert result["ok"] is True
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "# Decision Log" in readme
    assert "## By status" in readme


def test_index_unknown_status_falls_back_to_capitalized_label(tmp_path):
    _write_adr(
        tmp_path, "0001-use-kafka.md",
        id_="ADR-0001", title="Use Kafka", status="unknown", date="2026-08-01",
        tags=[], affected_paths=[],
    )

    result = index.run(SimpleNamespace(dir=str(tmp_path), locale="fr"))

    assert result["ok"] is True
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "### Unknown" in readme
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_index.py -v`
Expected: FAIL — `index.run` doesn't accept/use a locale yet, headers stay English-only.

- [ ] **Step 3: Extend the implementation**

In `skills/adr-toolkit/scripts/commands/index.py`, add the import:

```python
from scripts.core.locale import load_locale
```

Replace `run`'s body up to the `README.md` write:

```python
def run(args) -> dict:
    adr_dir = Path(args.dir)
    locale = getattr(args, "locale", None) or "en"
    strings = load_locale(locale)
    entries = []
    warnings = []

    for entry in sorted(adr_dir.glob("*.md")):
        if entry.name in SKIP_FILES:
            continue
        parsed = identifiers.parse_filename(entry.name)
        if parsed is None:
            continue
        try:
            data, _ = fm.parse(entry.read_text(encoding="utf-8"))
        except fm.FrontmatterError as exc:
            warnings.append({"code": "BAD_FRONTMATTER", "file": entry.name, "detail": str(exc)})
            continue
        entries.append({
            "id": data.get("id", f"ADR-{parsed[0]:04d}"),
            "filename": entry.name,
            "title": data.get("title", parsed[1]),
            "status": data.get("status", "unknown"),
            "date": data.get("date", ""),
            "tags": data.get("tags", []),
            "affected_paths": data.get("affected_paths", []),
        })

    (adr_dir / "README.md").write_text(_render(entries, strings), encoding="utf-8")

    return {
        "ok": True,
        "operation": "index",
        "count": len(entries),
        "path": str(adr_dir / "README.md"),
        "warnings": warnings,
    }
```

Replace `_render` to take and use `strings`:

```python
def _render(entries: list, strings: dict) -> str:
    lines = [f"# {strings['decision_log_title']}", ""]

    lines.append(f"## {strings['by_status']}")
    lines.append("")
    by_status: dict = {}
    for entry in entries:
        by_status.setdefault(entry["status"], []).append(entry)
    for status in sorted(by_status):
        label = strings.get(f"status.{status}", status.capitalize())
        lines.append(f"### {label}")
        for entry in sorted(by_status[status], key=lambda e: e["filename"]):
            lines.append(f"- [{entry['id']} — {entry['title']}]({entry['filename']})")
        lines.append("")

    lines.append(f"## {strings['by_tag']}")
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

    lines.append(f"## {strings['by_affected_path']}")
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

    lines.append(f"## {strings['chronological']}")
    lines.append("")
    for entry in sorted(entries, key=lambda e: e["date"], reverse=True):
        lines.append(f"- {entry['date']} — [{entry['id']} — {entry['title']}]({entry['filename']})")

    return "\n".join(lines) + "\n"
```

In `skills/adr-toolkit/scripts/adr.py`, find the `p_index` subparser and add a `--locale` argument:

```python
    p_index = sub.add_parser("index")
    p_index.add_argument("--dir", default="docs/decisions")
    p_index.add_argument("--locale", default="en")
    p_index.add_argument("--json", action="store_true")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_index.py -v`
Expected: PASS (all prior cases plus these 3)

Then run the full suite:

Run: `python -m pytest tests/unit tests/integration -v`
Expected: PASS (no regressions — `test_check_workflow.py` and `test_record_workflow.py` both call `index` without `--locale`, which must still default to English)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/scripts/commands/index.py skills/adr-toolkit/scripts/adr.py \
        tests/unit/test_index.py
git commit -m "feat: add --locale to index for localized README generation"
```

---

### Task 3: `SKILL.md` — agent language-detection instruction

**Files:**
- Modify: `skills/adr-toolkit/SKILL.md`
- Test: `tests/unit/test_skill_manifest.py` (add case)

**Interfaces:**
- Consumes: `index --locale` (Task 2, referenced by name only — this is a documentation task, not a code dependency).
- Produces: the agent-facing instruction that closes the loop between "the agent detects a language" and "the agent tells `index` to use it."

- [ ] **Step 1: Write the failing test**

Append to `tests/unit/test_skill_manifest.py`:

```python
def test_skill_md_documents_locale_detection():
    _, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    assert "--locale" in body
    assert "fr" in body and "ja" in body and "ko" in body and "zh" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_skill_manifest.py -v`
Expected: FAIL — no locale instruction exists yet.

- [ ] **Step 3: Add the instruction**

In `skills/adr-toolkit/SKILL.md`, add a new subsection right after `## Workflow contract` and before `## INIT (scaffolding only)`:

```markdown
## Language

Detect the language of the user's own request (English, French, Japanese,
Korean, or Chinese) and compose every question and report you write in
that language — English is the default when the language can't be
determined. This applies only to what you write yourself; it does not
change any file content the user themselves wrote in a different
language, and it does not translate `SKILL.md`'s own instructions.

When you run `index`, pass the same locale as a two-letter code so the
generated `docs/decisions/README.md` headers match
(`--locale en|fr|ja|ko|zh`, defaulting to `en` when omitted):

```bash
python skills/adr-toolkit/scripts/adr.py index --dir docs/decisions --locale fr --json
```
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_skill_manifest.py -v`
Expected: PASS (all prior cases plus this one)

- [ ] **Step 5: Commit**

```bash
git add skills/adr-toolkit/SKILL.md tests/unit/test_skill_manifest.py
git commit -m "docs: instruct the agent to detect language and pass index --locale"
```

---

### Task 4: Codex CLI adapter — manifest, README, structural test, manual verification

**Files:**
- Create: `adapters/codex/.codex-plugin/plugin.json`
- Create: `adapters/codex/README.md`
- Test: `tests/unit/test_codex_adapter.py`

**Interfaces:**
- Consumes: nothing (manifest is static JSON).
- Produces: nothing consumed by later tasks — adapters are independent leaves.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_codex_adapter.py
import json
from pathlib import Path

MANIFEST = (
    Path(__file__).resolve().parent.parent.parent
    / "adapters" / "codex" / ".codex-plugin" / "plugin.json"
)


def test_manifest_is_valid_json_with_required_fields():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["name"] == "adr-toolkit"


def test_manifest_has_no_extra_undocumented_top_level_keys():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert set(data.keys()) <= {"$schema", "name", "description"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_codex_adapter.py -v`
Expected: FAIL — manifest doesn't exist.

- [ ] **Step 3: Write the manifest and README**

```json
// adapters/codex/.codex-plugin/plugin.json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "adr-toolkit",
  "description": "Initialize, record, and check Architecture Decision Records by inspecting the repository and existing decisions before asking questions."
}
```

```markdown
<!-- adapters/codex/README.md -->
# Codex CLI adapter

Follows the cross-vendor Agent Plugins 1.0.0 standard
(`github.com/agentplugins/agent-plugins-spec`), which Codex CLI adopted
2026-08-07. This manifest needs only `name` — no `"skills"` key, since
Agent Plugins auto-discovers a sibling `skills/` directory.

## Install

1. Copy this repo's `skills/adr-toolkit/` package somewhere Codex can
   reach it, then symlink it under this adapter's plugin directory as
   `skills/adr-toolkit` (a sibling of `plugin.json`, inside
   `.codex-plugin/`):

   ```bash
   mkdir -p adapters/codex/.codex-plugin/skills
   ln -s "$(pwd)/skills/adr-toolkit" adapters/codex/.codex-plugin/skills/adr-toolkit
   ```

2. Point Codex at `adapters/codex/.codex-plugin/` per Codex's own plugin
   install documentation (`codex --help` documents the exact
   install/reload subcommand — it may change as the Agent Plugins
   standard matures, since this adapter shipped within days of the
   standard's own release).
3. Confirm Codex lists `adr-toolkit` as an available skill, then run
   `python skills/adr-toolkit/scripts/adr.py preflight --json` from your
   target repository to confirm the script layer works standalone.

The symlink is created at install time, not committed to this repo —
committing a real symlink breaks on Windows checkouts that don't have
`core.symlinks` enabled, which this project's CI can't assume.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_codex_adapter.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Manual end-to-end verification**

`codex` CLI (0.151.0) is installed in this environment — actually perform this install and record the real transcript in your task report (not a hypothetical):

```bash
mkdir -p /tmp/adr-toolkit-codex-verify && cd /tmp/adr-toolkit-codex-verify
git init -q
mkdir -p .codex-plugin/skills
ln -s "<absolute-path-to-this-repo>/skills/adr-toolkit" .codex-plugin/skills/adr-toolkit
cp "<absolute-path-to-this-repo>/adapters/codex/.codex-plugin/plugin.json" .codex-plugin/plugin.json
codex --help
# ^ read this output to find the actual plugin-list/plugin-install subcommand —
#   do not guess a subcommand name; Codex's plugin CLI surface is new as of
#   2026-08-07 and this plan cannot assert its exact flags with confidence.
#   Use whatever subcommand codex --help documents to confirm the adapter
#   is discoverable, then run the toolkit directly to prove the symlinked
#   skill actually works end to end:
python .codex-plugin/skills/adr-toolkit/scripts/adr.py preflight --json
python .codex-plugin/skills/adr-toolkit/scripts/adr.py init --dir docs/decisions --json
python .codex-plugin/skills/adr-toolkit/scripts/adr.py validate --dir docs/decisions --json
```

Record in the task report: the exact `codex --help` output relevant to plugin discovery, whether Codex actually lists `adr-toolkit`, and the `preflight`/`init`/`validate` JSON output proving the symlinked skill runs correctly from inside a Codex-style plugin layout. If Codex's plugin CLI doesn't expose a discovery command yet (the standard is very new), say so plainly and rely on the direct script execution as the verification instead — do not claim a Codex-side discovery check that didn't happen.

- [ ] **Step 6: Commit**

```bash
git add adapters/codex tests/unit/test_codex_adapter.py
git commit -m "feat: add Codex CLI adapter manifest and install docs"
```

---

### Task 5: Gemini CLI adapter — manifest, README, structural test, manual verification

**Files:**
- Create: `adapters/gemini-cli/gemini-extension.json`
- Create: `adapters/gemini-cli/README.md`
- Test: `tests/unit/test_gemini_cli_adapter.py`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_gemini_cli_adapter.py
import json
from pathlib import Path

MANIFEST = (
    Path(__file__).resolve().parent.parent.parent
    / "adapters" / "gemini-cli" / "gemini-extension.json"
)


def test_manifest_is_valid_json_with_required_fields():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["name"] == "adr-toolkit"


def test_manifest_name_uses_dashes_not_underscores_or_spaces():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert " " not in data["name"]
    assert "_" not in data["name"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_gemini_cli_adapter.py -v`
Expected: FAIL — manifest doesn't exist.

- [ ] **Step 3: Write the manifest and README**

```json
// adapters/gemini-cli/gemini-extension.json
{
  "name": "adr-toolkit",
  "version": "0.1.0",
  "description": "Initialize, record, and check Architecture Decision Records by inspecting the repository and existing decisions before asking questions."
}
```

```markdown
<!-- adapters/gemini-cli/README.md -->
# Gemini CLI adapter

Gemini CLI extensions declare themselves via a root `gemini-extension.json`
(see `geminicli.com/docs/extensions/reference/`), expecting a sibling
`skills/` directory holding `SKILL.md` files.

## Install

1. Symlink this repo's `skills/adr-toolkit/` package under this adapter's
   directory:

   ```bash
   mkdir -p adapters/gemini-cli/skills
   ln -s "$(pwd)/skills/adr-toolkit" adapters/gemini-cli/skills/adr-toolkit
   ```

2. Install the extension per Gemini CLI's own extension-install command
   (`gemini extensions install <path-to-adapters/gemini-cli>` at the time
   this adapter was verified — confirm against `gemini --help` /
   `gemini extensions --help`, since command surfaces move faster than
   this file).
3. Confirm Gemini CLI lists `adr-toolkit` as an installed extension, then
   run `python skills/adr-toolkit/scripts/adr.py preflight --json` from
   your target repository to confirm the script layer works standalone.

The symlink is created at install time, not committed to this repo —
committing a real symlink breaks on Windows checkouts that don't have
`core.symlinks` enabled, which this project's CI can't assume.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_gemini_cli_adapter.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Manual end-to-end verification**

`gemini` CLI (0.46.0) is installed in this environment — actually perform this install and record the real transcript in your task report:

```bash
mkdir -p /tmp/adr-toolkit-gemini-verify && cd /tmp/adr-toolkit-gemini-verify
git init -q
mkdir -p skills
ln -s "<absolute-path-to-this-repo>/skills/adr-toolkit" skills/adr-toolkit
cp "<absolute-path-to-this-repo>/adapters/gemini-cli/gemini-extension.json" gemini-extension.json
gemini extensions --help
# ^ read this output to find the actual install/list subcommand — do not
#   guess; confirm the real syntax before running it.
# Then, whatever the real install command is, run it against this directory
# and confirm gemini lists adr-toolkit as an installed extension. Finally
# prove the symlinked skill runs correctly end to end:
python skills/adr-toolkit/scripts/adr.py preflight --json
python skills/adr-toolkit/scripts/adr.py init --dir docs/decisions --json
python skills/adr-toolkit/scripts/adr.py validate --dir docs/decisions --json
```

Record in the task report: the exact `gemini extensions --help` output relevant to install/discovery, whether Gemini CLI actually lists `adr-toolkit` after installing, and the `preflight`/`init`/`validate` JSON output.

- [ ] **Step 6: Commit**

```bash
git add adapters/gemini-cli tests/unit/test_gemini_cli_adapter.py
git commit -m "feat: add Gemini CLI adapter manifest and install docs"
```

---

### Task 6: Antigravity CLI adapter — manifest, README, structural test only

**Files:**
- Create: `adapters/antigravity/plugin.json`
- Create: `adapters/antigravity/README.md`
- Test: `tests/unit/test_antigravity_adapter.py`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing consumed by later tasks.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_antigravity_adapter.py
import json
import re
from pathlib import Path

MANIFEST = (
    Path(__file__).resolve().parent.parent.parent
    / "adapters" / "antigravity" / "plugin.json"
)

NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def test_manifest_is_valid_json_with_required_fields():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["name"] == "adr-toolkit"


def test_manifest_name_matches_antigravity_naming_rule():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert NAME_RE.match(data["name"]), "name must be alphanumeric, hyphens, or underscores only"


def test_manifest_schema_field_points_at_antigravity_schema():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["$schema"] == "https://antigravity.google/schemas/v1/plugin.json"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_antigravity_adapter.py -v`
Expected: FAIL — manifest doesn't exist.

- [ ] **Step 3: Write the manifest and README**

```json
// adapters/antigravity/plugin.json
{
  "$schema": "https://antigravity.google/schemas/v1/plugin.json",
  "name": "adr-toolkit",
  "description": "Initialize, record, and check Architecture Decision Records by inspecting the repository and existing decisions before asking questions."
}
```

```markdown
<!-- adapters/antigravity/README.md -->
# Antigravity CLI adapter

Antigravity plugins are a `plugin.json` marker file plus optional sibling
directories (`skills/`, `agents/`, `rules/`), per
`antigravity.google/docs/cli/plugins/`. This manifest needs only `name`.

## Install

1. Symlink this repo's `skills/adr-toolkit/` package under this adapter's
   directory:

   ```bash
   mkdir -p adapters/antigravity/skills
   ln -s "$(pwd)/skills/adr-toolkit" adapters/antigravity/skills/adr-toolkit
   ```

2. Install per Antigravity's own plugin-install documentation.
3. Confirm Antigravity lists `adr-toolkit`, then run
   `python skills/adr-toolkit/scripts/adr.py preflight --json` from your
   target repository to confirm the script layer works standalone.

**Verification status:** this adapter's manifest and directory layout are
verified against Antigravity's published schema, but — unlike the Codex
and Gemini CLI adapters — no end-to-end install-and-run was performed,
because no `antigravity` CLI binary was available in the development
environment that built this adapter. Treat it as unverified until someone
with the actual CLI confirms it, and update this note when they do.

The symlink is created at install time, not committed to this repo —
committing a real symlink breaks on Windows checkouts that don't have
`core.symlinks` enabled, which this project's CI can't assume.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_antigravity_adapter.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add adapters/antigravity tests/unit/test_antigravity_adapter.py
git commit -m "feat: add Antigravity CLI adapter manifest (structural verification only)"
```

---

### Task 7: `scripts/sync_version.py` — repo-root version synchronization

**Files:**
- Create: `scripts/sync_version.py`
- Test: `tests/unit/test_sync_version.py`

**Interfaces:**
- Consumes: nothing (reads `VERSION` and manifest paths passed as arguments, for testability against fixtures rather than the real repo tree).
- Produces: `sync(version_file: Path, manifest_specs: list, check_only: bool) -> list` where `manifest_specs` is a list of `(path, json_key_path)` tuples, and the return value is the list of paths that were (or would be) changed; `sync_skill_md(version_file: Path, skill_md_path: Path, check_only: bool) -> bool` for the one non-JSON duplicate (`SKILL.md`'s YAML frontmatter `version:` line — `scripts/sync_version.py` lives at the repo root, outside `skills/adr-toolkit/`, so it cannot import that package's own `core.frontmatter` module without an ambiguous `scripts.*` import path collision between the two same-named `scripts/` directories; a small targeted regex substitution on just the `version:` line avoids that entirely and avoids re-serializing — and risking reformatting — the rest of the file). `main(argv=None) -> int` for CLI use. Used by Task 8 (CI wiring — invoked as a subprocess, not imported).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_sync_version.py
import json

from scripts.sync_version import sync

MANIFEST_SPECS = [("plugin.json", ["version"]), ("nested.json", ["meta", "version"])]


def _write(tmp_path, name, data):
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_sync_writes_matching_version_into_every_manifest(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    plugin = _write(tmp_path, "plugin.json", {"name": "x", "version": "0.0.0"})
    nested = _write(tmp_path, "nested.json", {"meta": {"version": "0.0.0"}})

    changed = sync(version_file, [(plugin, ["version"]), (nested, ["meta", "version"])], check_only=False)

    assert json.loads(plugin.read_text())["version"] == "1.2.3"
    assert json.loads(nested.read_text())["meta"]["version"] == "1.2.3"
    assert set(changed) == {plugin, nested}


def test_sync_is_idempotent_when_already_synced(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    plugin = _write(tmp_path, "plugin.json", {"name": "x", "version": "1.2.3"})

    changed = sync(version_file, [(plugin, ["version"])], check_only=False)

    assert changed == []


def test_check_only_mode_reports_drift_without_writing(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    plugin = _write(tmp_path, "plugin.json", {"name": "x", "version": "0.0.0"})

    changed = sync(version_file, [(plugin, ["version"])], check_only=True)

    assert changed == [plugin]
    assert json.loads(plugin.read_text())["version"] == "0.0.0"


def test_manifest_missing_a_version_key_is_skipped_not_added(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    frontmatter_like = _write(tmp_path, "nokey.json", {"name": "x"})

    changed = sync(version_file, [(frontmatter_like, ["version"])], check_only=False)

    assert changed == []
    assert "version" not in json.loads(frontmatter_like.read_text())


def test_sync_skill_md_updates_frontmatter_version_line(tmp_path):
    from scripts.sync_version import sync_skill_md

    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(
        "---\nname: adr-toolkit\nversion: 0.0.0\n---\n\n# ADR Toolkit\n", encoding="utf-8",
    )

    changed = sync_skill_md(version_file, skill_md, check_only=False)

    assert changed is True
    updated = skill_md.read_text(encoding="utf-8")
    assert "version: 1.2.3" in updated
    assert "name: adr-toolkit" in updated  # untouched fields survive unchanged


def test_sync_skill_md_check_only_does_not_write(tmp_path):
    from scripts.sync_version import sync_skill_md

    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\nversion: 0.0.0\n---\n\nBody\n", encoding="utf-8")

    changed = sync_skill_md(version_file, skill_md, check_only=True)

    assert changed is True
    assert "version: 0.0.0" in skill_md.read_text(encoding="utf-8")


def test_sync_skill_md_idempotent_when_already_synced(tmp_path):
    from scripts.sync_version import sync_skill_md

    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\nversion: 1.2.3\n---\n\nBody\n", encoding="utf-8")

    changed = sync_skill_md(version_file, skill_md, check_only=False)

    assert changed is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/unit/test_sync_version.py -v`
Expected: FAIL — module doesn't exist.

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/sync_version.py
#!/usr/bin/env python3
"""Sync skills/adr-toolkit/VERSION into every manifest that duplicates it.

Repo tooling — not part of the distributable skills/adr-toolkit/ package.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = REPO_ROOT / "skills" / "adr-toolkit" / "VERSION"
SKILL_MD_PATH = REPO_ROOT / "skills" / "adr-toolkit" / "SKILL.md"

# (manifest path relative to REPO_ROOT, key path within its JSON)
# Only manifests confirmed to carry their own "version" field are listed —
# a manifest with no such field is never modified to add one.
MANIFEST_SPECS = [
    (REPO_ROOT / ".claude-plugin" / "plugin.json", ["version"]),
    (REPO_ROOT / "adapters" / "gemini-cli" / "gemini-extension.json", ["version"]),
]

VERSION_LINE_RE = re.compile(r"^version:\s*\S+$", re.MULTILINE)


def sync(version_file: Path, manifest_specs: list, check_only: bool) -> list:
    version = version_file.read_text(encoding="utf-8").strip()
    changed = []
    for path, key_path in manifest_specs:
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        target = data
        for key in key_path[:-1]:
            if key not in target:
                target = None
                break
            target = target[key]
        if target is None or key_path[-1] not in target:
            continue
        if target[key_path[-1]] == version:
            continue
        changed.append(path)
        if not check_only:
            target[key_path[-1]] = version
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return changed


def sync_skill_md(version_file: Path, skill_md_path: Path, check_only: bool) -> bool:
    if not skill_md_path.is_file():
        return False
    version = version_file.read_text(encoding="utf-8").strip()
    text = skill_md_path.read_text(encoding="utf-8")
    match = VERSION_LINE_RE.search(text)
    if match is None or match.group() == f"version: {version}":
        return False
    if not check_only:
        new_text = VERSION_LINE_RE.sub(f"version: {version}", text, count=1)
        skill_md_path.write_text(new_text, encoding="utf-8")
    return True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    changed = sync(VERSION_FILE, MANIFEST_SPECS, check_only=args.check)
    if sync_skill_md(VERSION_FILE, SKILL_MD_PATH, check_only=args.check):
        changed.append(SKILL_MD_PATH)

    if args.check and changed:
        for path in changed:
            print(f"drift: {path.relative_to(REPO_ROOT)}", file=sys.stderr)
        return 1
    for path in changed:
        print(f"synced: {path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/unit/test_sync_version.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/sync_version.py tests/unit/test_sync_version.py
git commit -m "feat: add version sync script for duplicated manifest version fields"
```

---

### Task 8: CI drift check + `release.yml`

**Files:**
- Modify: `.github/workflows/test.yml`
- Create: `.github/workflows/release.yml`
- Test: none (GitHub Actions workflow YAML isn't unit-testable in this stack; reviewed by reading it against `test.yml`'s existing conventions, per spec §17.4)

**Interfaces:**
- Consumes: `scripts/sync_version.py --check` (Task 7), invoked as a subprocess by CI, not imported.
- Produces: nothing consumed by a later task — this is the plan's last task.

- [ ] **Step 1: Add the drift-check step to `test.yml`**

In `.github/workflows/test.yml`, add a step after `Run tests` in the existing `pytest` job:

```yaml
      - name: Run tests
        run: python -m pytest tests/unit tests/integration -v
      - name: Check manifest versions are in sync
        run: python scripts/sync_version.py --check
```

- [ ] **Step 2: Verify the check step behaves correctly, locally**

Run: `python scripts/sync_version.py --check`
Expected: exit code 0, no output — the repo's real manifests are already in sync with `VERSION` (`0.1.0`), since Task 7 only reads/checks and Task 8 doesn't change any version value.

- [ ] **Step 3: Write `release.yml`**

```yaml
# .github/workflows/release.yml
name: release

on:
  push:
    tags:
      - "v*"

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: pip install pytest
      - name: Run tests
        run: python -m pytest tests/unit tests/integration -v
      - name: Verify manifest versions match the tag
        run: python scripts/sync_version.py --check
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
```

- [ ] **Step 4: Confirm the workflow is syntactically valid YAML**

Run: `python -c "import yaml, sys; yaml.safe_load(open('.github/workflows/release.yml'))"`
Expected: no output, exit code 0 (`pyyaml` ships with most CI runner images; if it's not installed locally, `python -c "import json,sys; import yaml"` failing with `ModuleNotFoundError` is fine to note in the task report — the workflow's real validation happens when GitHub Actions parses it on the next tag push, which this task cannot trigger)

- [ ] **Step 5: Run the full suite one last time and commit**

Run: `python -m pytest tests/unit tests/integration -v`
Expected: PASS (all tests from Plans 1-4)

```bash
git add .github/workflows/test.yml .github/workflows/release.yml
git commit -m "feat: add version-drift CI check and tag-triggered release workflow"
```

---

## Plan self-review notes

- **Spec coverage:** §17.1 (i18n scope/mechanism) → Tasks 1, 2, 3. §17.2 (adapter formats, symlink pattern, manual verification split by CLI availability) → Tasks 4, 5, 6. §17.3 (version sync, release automation) → Tasks 7, 8. §17.4 (testing strategy) → each task's own test file; adapter manual-verification steps map to §17.4's "not an automated pytest case" note. §8/§9's original product framing is fully covered by §17's refinement, so no separate tasks needed beyond what §17 already resolves.
- **Type consistency checked:** `load_locale`'s return type (`dict`, Task 1) matches `index.py`'s `strings` parameter (Task 2) exactly, including the `status.<name>` key convention used consistently in both the JSON files and `_render`'s lookup. `sync_version.sync`'s `(path, key_path)` tuple shape (Task 7) matches `MANIFEST_SPECS`'s own construction in the same file — no second, incompatible shape introduced elsewhere. No adapter task (4, 5, 6) is consumed by any other task, matching their "independent leaves" Interfaces note — verified none of Tasks 1-3 or 7-8 import anything from `adapters/`.
- **Self-caught during review:** the spec's §17.3 names three duplicate version locations (`VERSION`, `.claude-plugin/plugin.json`, `SKILL.md`'s frontmatter), but the plan's first draft of `MANIFEST_SPECS` covered only the two JSON manifests — `sync()`'s JSON-only design can't touch `SKILL.md`, which is markdown with YAML frontmatter, not JSON. Fixed by adding a separate `sync_skill_md()` using a targeted regex substitution on just the `version:` line, rather than importing `skills/adr-toolkit/`'s own `core.frontmatter` module (which would collide with `scripts/sync_version.py`'s own `scripts.*` import path — two same-named `scripts/` directories at different roots) or risking a full frontmatter re-serialize reformatting fields outside this task's scope. Also caught and fixed a regex subtlety in that same substitution: a trailing `\s*` before `$` combined with `\s`'s newline-matching under `re.MULTILINE` could have let the match creep across blank lines; the final pattern (`^version:\s*\S+$`, no trailing `\s*`) doesn't have that failure mode.
- **No placeholders found.** The adapter tasks' "read `codex --help`/`gemini extensions --help` before running the real subcommand" steps are deliberate — this plan cannot assert an unverified CLI flag as fact (that mistake already cost Plan 1 a fix round on the Claude Code adapter), so the concrete, runnable instruction is "investigate via `--help`, then use what it says," not a placeholder for missing code.
