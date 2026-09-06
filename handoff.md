# handoff.md

## Current task

Hotfix v1.1.1: closed two gaps discovered while deploying v1.1.0 —
`.claude-plugin/marketplace.json` missing the `owner` field (blocked
`claude plugin marketplace add` on Claude Code v2.1.263) and `pyproject.toml`
not in `scripts/sync_version.py`'s sync surface (v1.1.0 GitHub Release shipped a
1.0.1 wheel/sdist). Both fixes are landed on `fix/v1.1.1-hotfix`; ready to cut a
release.

## Touched files

- `.claude-plugin/marketplace.json` — added `$schema`, top-level `description`,
  `owner.name` (mirrors the working `Agent-toolkit/.claude-plugin/marketplace.json`).
- `scripts/sync_version.py` — added `TOML_VERSION_SPECS` (`pyproject.toml`
  `[project]` table), `TOML_VERSION_LINE_RE`, `_section_header_re()`,
  `sync_toml_version()`. `require_known_paths()` now asserts the `[project]`
  table is present. `main()` calls `sync_toml_version()`.
- `tests/unit/test_sync_version.py` — added 6 regression tests for TOML sync
  (writes, idempotent, check-only, missing-section, other-table-untouched,
  real-pyproject-drift guard).
- `skills/adr-toolkit/VERSION`, `SKILL.md` frontmatter, `.claude-plugin/plugin.json`,
  `adapters/gemini-cli/gemini-extension.json`, `adapters/antigravity/plugin.json`,
  `pyproject.toml` — all synced to 1.1.1 via `scripts/sync_version.py`.
- `changelog.md` — new `## v1.1.1 (2026-09-06)` section.
- `handoff.md` — this file.

## Verification (local, Python 3.13 standalone — pytest not installed user-scope)

- `scripts/sync_version.py --check`: **exit 0** (no drift, including pyproject.toml).
- 6 new TOML sync tests re-run as standalone assertions: **all pass**.
- `script/sync_version.py` and `tests/unit/test_sync_version.py` parse with
  `ast.parse`: OK.
- Real-repo guard: `pyproject.toml` `[project] version` reports `1.1.1`, matches
  `skills/adr-toolkit/VERSION`.

## Next step

1. Merge `fix/v1.1.1-hotfix` → `develop` (PR, CI must pass — including the
   version-drift job, which now also checks pyproject.toml).
2. Open `release/v1.1.1` → `master` PR; after CI passes (release.yml runs the
   full suite + tag == VERSION check), merge.
3. Back-merge `master` → `develop`.
4. Tag `v1.1.1` from `master` and push — `release.yml` runs pytest +
   sync_version --check + tag == VERSION, then publishes a GitHub Release with
   the skill tarball + sha256 + Python wheel/sdist, and publishes to PyPI via
   Trusted Publisher (`continue-on-error: true`, tracked in improvements.md).
5. After release, refresh the local installs on the four harnesses
   (Claude Code `~/.claude/skills/` symlink, Codex `~/.codex/skills/`,
   Antigravity `~/.gemini/config/plugins/adr-toolkit/skills/adr-toolkit/`,
   Cline `~/.agents/skills/`) to v1.1.1 — the same flow used to bring them to
   v1.1.0 in the previous session.

## Open risks

- PyPI Trusted Publisher still `continue-on-error: true` — known, tracked.
- Cline adapter still manually verified; `harness-parity` not covering Cline yet
  (Medium backlog item from PR #36).
- Inherits prior Open risks (ruleset context sync, deferred automation).
