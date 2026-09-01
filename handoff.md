# handoff.md

## Current task (2026-09-01)

Examples redesign, Korean documentation, automated verification pipeline, `v0.2.1` release, and PR Conventional Commits automation.

### Implemented this session:

- **Examples Redesign (`examples/`)**: Created 4 structured, representative use-case guides (`basic-usage.md`, `check-constraints.md`, `graph-visualization.md`, `multilingual-adr.md`) using standard Scenario → Input → What Happens → Output format.
- **Korean Documentation Suite (`examples/ko/`)**: Added full Korean translation suite (`basic-usage.md`, `check-constraints.md`, `graph-visualization.md`, `multilingual-adr.md`, `README.md`).
- **Automated Verification Pipeline**:
  - `scripts/verify_examples.py`: `--check` (executes example workflows in isolated temp repo) & `--update` (auto-updates JSON output snippets when CLI outputs change).
  - `tests/integration/test_examples.py`: Integration test ensuring 100% executable example parity in `pytest`.
- **v0.2.1 Release**: Bumped version to `0.2.1`, synced manifests (`SKILL.md`, `.claude-plugin/plugin.json`, `adapters/gemini-cli/gemini-extension.json`), tagged `v0.2.1` on `master`, merged via Git Flow, and pushed to `origin`.
- **Git Pre-push Hook (`.githooks/pre-push`)**: Created pre-push hook configured via `git config core.hooksPath .githooks` to block direct local pushes to `develop` and `master`, enforcing PR-based merges.
- **PR Title Linter & PR Template**: Added `pr-title-check` CI job to `.github/workflows/test.yml` enforcing Conventional Commits format (`feat:`, `fix:`, `docs:`, etc.) and updated `.github/PULL_REQUEST_TEMPLATE.md` with explicit Examples Impact checklist for `feat:`/`fix:` changes.
- **Lifecycle Report**: Recorded automation strategy in `automated_examples_lifecycle_report.md` artifact.

## Touched files

- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/test.yml`
- `examples/` (`README.md`, `basic-usage.md`, `check-constraints.md`, `graph-visualization.md`, `multilingual-adr.md`)
- `examples/ko/` (`README.md`, `basic-usage.md`, `check-constraints.md`, `graph-visualization.md`, `multilingual-adr.md`)
- `scripts/verify_examples.py`
- `tests/integration/test_examples.py`
- `skills/adr-toolkit/VERSION`
- `skills/adr-toolkit/SKILL.md`
- `.claude-plugin/plugin.json`
- `adapters/gemini-cli/gemini-extension.json`
- `changelog.md`
- `handoff.md`

## Next step

1. Monitor CI run for `pr-title-check` and `examples-drift` on upcoming PRs into `develop`.
2. When new features (`feat:`) or bug fixes (`fix:`) are added in future PRs, run `python3 scripts/verify_examples.py --check` and `--update` to keep examples automatically in sync.

## Open risk

- None. All 396 tests, version drift checks, and example verification checks pass cleanly across Python 3.9 & 3.12.
