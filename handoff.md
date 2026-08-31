# handoff.md

## Current task (2026-08-31)

Examples redesign, Korean documentation, automated verification pipeline, and release of `v0.2.1`.

Implemented this session:

- Redesigned `examples/` directory into 4 structured, realistic use cases with standardized `Scenario`, `Input`, `What Happens`, and `Output` sections:
  - `examples/basic-usage.md`: Core INIT → RECORD → INDEX workflow.
  - `examples/check-constraints.md`: Mechanical constraint enforcement (`forbidden_import`), `check --uncommitted`, resolution options, and exception registration.
  - `examples/graph-visualization.md`: Decision evolution via `supersede` and exporting Mermaid / SVG relationship graphs.
  - `examples/multilingual-adr.md`: Localized Korean (`--locale ko`) repository default with approved ASCII filename slug (`--slug`).
- Added complete Korean documentation suite under [`examples/ko/`](examples/ko/README.md) (`basic-usage.md`, `check-constraints.md`, `graph-visualization.md`, `multilingual-adr.md`, `README.md`).
- Built automated example verification and update script `scripts/verify_examples.py`:
  - `--check`: Runs isolated execution of all example workflows to ensure CLI logic compatibility and prevent doc drift.
  - `--update`: Re-executes CLI commands to update example output snippets automatically when `adr.py` CLI outputs or schemas change.
- Added pytest integration test `tests/integration/test_examples.py` (`test_examples_execution_and_schema_parity`).
- Bumped version to `0.2.1` across manifests (`skills/adr-toolkit/VERSION`, `SKILL.md`, `.claude-plugin/plugin.json`, `adapters/gemini-cli/gemini-extension.json`).
- Updated `examples/README.md` index table and linked `examples/` from root `README.md`.
- Public repository hygiene: `CONTRIBUTING.md`, `SECURITY.md`, `.github/PULL_REQUEST_TEMPLATE.md`, `CODE_OF_CONDUCT.md`, `.github/ISSUE_TEMPLATE/{bug_report,feature_request}.md`.

## Latest local verification

- `python3 -m pytest -q` -> `396 passed`
- `python3 scripts/verify_examples.py --check` -> clean exit 0
- `python3 scripts/sync_version.py --check` -> clean exit 0
