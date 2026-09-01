# changelog.md

Lightweight human-readable summary of meaningful repository changes.

## Unreleased

- `core/contracts.py` now covers all 16 commands' output shapes (was 2).
- `PathEscapesRootError` (added in the prior session's path-escape fix)
  is now caught at all 7 call sites and reported as a structured
  `PATH_ESCAPES_ROOT` error instead of falling through to a generic
  internal error. All 6 domain exception classes now share a common
  `AdrToolkitError` base with a stable `error_code`.
- Added a test that fails if `schemas/*.json` and the runtime validators
  in `core/schema.py`/`core/exceptions.py` ever diverge -- without adding
  a `jsonschema` dependency.
- `core/contracts.py` now also covers CHECK's result shape.
- Added a sanity check proving `search`/`index` don't degrade
  catastrophically at 200 ADRs.
- `adr.py` now prints a one-line human-readable summary to stderr when
  stderr is a real terminal (set `ADR_TOOLKIT_NO_COLOR` to suppress);
  stdout's JSON contract and piped/redirected usage are unaffected.
- `--dir`/`--root` now reject a relative path that resolves outside the
  given root, closing a path-escape gap.
- CI now measures branch coverage (currently 93%) and fails below 85%.
- Added a `mypy --strict` CI gate over the fully-typed core modules
  (`atomic_io`, `telemetry`, the new `contracts` module of TypedDict result
  shapes).
- Added `adr.py --diagnostic` (must precede the operation name) to include
  an `elapsed_ms` timing field in the JSON result.
- Verified at the OS level (fork + SIGKILL) that a process killed mid-write
  never leaves a torn ADR file.
- Extracted a shared adapter-manifest validator (`scripts/adapter_sdk.py`)
  used by all 4 manifest-based harness adapters' tests.
- ADR and exception creation, and SUPERSEDE's two-file update, are now
  atomic and race-free under concurrent invocation (file locking + write to
  a temp file followed by an atomic rename).
- CHECK's author-supplied `constraints:` regex patterns now have a 0.25s
  evaluation timeout on Linux/macOS, closing a ReDoS risk (Windows CI is
  unaffected but not yet guarded — tracked in `improvements.md`).
- INDEX's generated decision-log README now escapes ADR titles, closing a
  Markdown link-injection risk.
- Uncaught errors now log a structured, correlation-ID-tagged JSON line to
  stderr (`ADR_TOOLKIT_LOG_LEVEL` controls the threshold) instead of
  disappearing silently; the same correlation ID appears in the stdout
  JSON error response.
- Added `.githooks/pre-push` script to block direct local `git push` to protected branches (`develop`, `master`)
  and direct contributors to use Pull Requests (`feature/*` / `fix/*`).
- Added Conventional Commits PR title validation job (`pr-title-check`) to GitHub Actions workflow (`.github/workflows/test.yml`)
  to enforce standard title format (`feat:`, `fix:`, `docs:`, etc.) for pull requests.
- Updated `.github/PULL_REQUEST_TEMPLATE.md` with Conventional Commits title format guide and an explicit Examples Impact checklist
  requiring example updates for `feat:` and `fix:` changes while skipping non-feature PRs.
- Fixed Windows CP1252 console encoding failure (`UnicodeEncodeError: 'charmap' codec can't encode character '✓'`) in `scripts/verify_examples.py` and `tests/integration/test_examples.py` by replacing non-ASCII symbols with ASCII tags (`[ok]`, `[error]`), reconfiguring stdout/stderr UTF-8 streams, and setting `PYTHONIOENCODING=utf-8` in subprocess calls.
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
