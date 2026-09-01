# changelog.md

Lightweight human-readable summary of meaningful repository changes.

## Unreleased

- Added `.githooks/pre-push` script to block direct local `git push` to protected branches (`develop`, `master`)
  and direct contributors to use Pull Requests (`feature/*` / `fix/*`).
- Added Conventional Commits PR title validation job (`pr-title-check`) to GitHub Actions workflow (`.github/workflows/test.yml`)
  to enforce standard title format (`feat:`, `fix:`, `docs:`, etc.) for pull requests.
- Updated `.github/PULL_REQUEST_TEMPLATE.md` with Conventional Commits title format guide and an explicit Examples Impact checklist
  requiring example updates for `feat:` and `fix:` changes while skipping non-feature PRs.
- Fixed Windows CP1252 console encoding failure (`UnicodeEncodeError: 'charmap' codec can't encode character '\u2713'`) in `scripts/verify_examples.py` and `tests/integration/test_examples.py` by replacing non-ASCII symbols with ASCII tags (`[ok]`, `[error]`), reconfiguring stdout/stderr UTF-8 streams, and setting `PYTHONIOENCODING=utf-8` in subprocess calls.
- Added untracked manifest discovery (`discover_untracked_manifests`) in `scripts/sync_version.py` to automatically prevent untracked plugin/extension manifests from being added in PRs without version/description tracking.
- Added `.pre-commit-config.yaml` for local contributor pre-commit checks and updated `CONTRIBUTING.md` with manifest governance guidelines.
- Enhanced Antigravity CLI (`agy`) plugin manifest (`adapters/antigravity/plugin.json`) with `version` tracking integrated into `scripts/sync_version.py`, expanded unit test assertions in `test_antigravity_adapter.py` (including symlink layout simulation) and `test_readme.py`, and updated `README.md` documentation.

## v0.2.1 (2026-08-31)

- Redesigned and expanded `examples/` into representative, structured usage guides
  (`basic-usage.md`, `check-constraints.md`, `graph-visualization.md`, and
  `multilingual-adr.md`) with standardized Scenario, Input, What Happens, and Output sections.
- Added a full Korean documentation suite under [`examples/ko/`](examples/ko/README.md)
  (including `basic-usage.md`, `check-constraints.md`, `graph-visualization.md`, and `multilingual-adr.md`).
- Created `scripts/verify_examples.py` and `tests/integration/test_examples.py` to
  automatically verify that all documented example commands execute cleanly and to auto-update
  example output snippets when core `adr.py` logic or schemas change.

- Added a `harness-parity` CI job that installs the real Codex CLI and
  Gemini CLI and drives their own plugin/extension commands (marketplace
  add, install, list) against this repo, then runs `preflight`/`init`/
  `validate` from the installed snapshot on every push and pull request —
  catching a broken adapter before a user hits it, not after.
- Added public repository readiness docs: `CONTRIBUTING.md`, `SECURITY.md`,
  and a pull request template covering ADR impact and local verification.
