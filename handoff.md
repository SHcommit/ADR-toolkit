# handoff.md

## Current task (2026-08-31)

Examples redesign, Korean documentation, automated verification pipeline, and version bump to `v0.2.1` on branch `feature/exemples-building`.

Implemented this session:

- Redesigned `examples/` directory into 4 structured, realistic use cases with standardized `Scenario`, `Input`, `What Happens`, and `Output` sections:
  - `examples/basic-usage.md`: Core INIT → RECORD → INDEX workflow.
  - `examples/check-constraints.md`: Mechanical constraint enforcement (`forbidden_import`), `check --uncommitted`, resolution options, and exception registration.
  - `examples/graph-visualization.md`: Decision evolution via `supersede` and exporting Mermaid / SVG relationship graphs.
  - `examples/multilingual-adr.md`: Localized Korean (`--locale ko`) repository default with approved ASCII filename slug (`--slug`).
- Added complete Korean documentation suite under [`examples/ko/`](file:///Users/yangseunghyeon/orca/workspaces/ADR-toolkit/seasnake/examples/ko/README.md) (`basic-usage.md`, `check-constraints.md`, `graph-visualization.md`, `multilingual-adr.md`, `README.md`).
- Built automated example verification and update script `scripts/verify_examples.py`:
  - `--check`: Runs isolated execution of all example workflows to ensure CLI logic compatibility and prevent doc drift.
  - `--update`: Re-executes CLI commands to update example output snippets automatically when `adr.py` CLI outputs or schemas change.
- Added pytest integration test `tests/integration/test_examples.py` (`test_examples_execution_and_schema_parity`).
- Updated `examples/README.md` index table and linked `examples/` from root `README.md`.
- Public repository hygiene: `CONTRIBUTING.md`, `SECURITY.md`,
  `.github/PULL_REQUEST_TEMPLATE.md`, `CODE_OF_CONDUCT.md`, and
  `.github/ISSUE_TEMPLATE/{bug_report,feature_request}.md`.
- Harness parity, manually re-verified end-to-end against the real CLIs
  installed on this machine (not just manifest-schema checks):
  - Codex CLI 0.151.0 -- `codex plugin marketplace add/add/list`, then
    `preflight`/`init`/`validate` from the installed snapshot, all
    `"ok": true`.
  - Gemini CLI 0.46.0 -- `gemini extensions validate/install/list`, then the
    same three commands from the installed snapshot, all `"ok": true`.
  - Antigravity CLI (`agy` 1.1.13) -- previously undocumented as available;
    `agy plugin validate/install/list` plus the same three commands all
    `"ok": true`. `adapters/antigravity/README.md` updated from "unverified"
    to a recorded transcript, matching the Codex/Gemini READMEs' format.
  - New `harness-parity` CI job (`.github/workflows/test.yml`) automates the
    Codex and Gemini checks above on every push/PR, pinned to the exact
    verified versions. Every step was dry-run locally against those same
    CLI versions before landing. Antigravity stays manual-only: `agy` has no
    npm/package-registry distribution, so a CI runner can't install it.
  - `project-roadmap.md`'s "Harness parity" section narrowed to what's
    actually still open: extending `harness-parity` past
    preflight/init/validate to check/search/graph/create, and automating
    Antigravity once it has an installable distribution.
- `project-roadmap.md` audited end-to-end against the codebase; confirmed no
  other section describes already-shipped work.

## Next step

Open or update a PR for `feature/project-roadmap-implements` into `develop`
so the new `harness-parity` CI job actually runs on GitHub's runners at
least once before being trusted (everything above was dry-run locally with
the same pinned CLI versions, but never through the real Actions runner).

The broader `v0.2.0` release gate still needs separate explicit owner approval
for each step:

1. Merge the PR into `develop`.
2. Cut a `release/*` branch into `master` and back into `develop`, per
   `AGENTS.md`'s Git Flow policy.
3. Push a `v0.2.0` tag on `master`; `.github/workflows/release.yml` then runs
   the full suite, verifies manifest versions against the tag, and publishes
   the GitHub Release.

Do not perform merge, release branch, push, or tag operations without explicit
owner approval. The repository owner has said the switch to public is coming
"soon" but deliberately not yet -- don't start the "Public and enterprise
governance" roadmap items (they're gated on the repo actually being public).

## Latest local verification

After `2f2f604` (current HEAD):

- `python3 -m pytest -q` -> `395 passed`
- `python3 scripts/sync_version.py --check` -> exit 0
- `adr.py validate --dir docs/decisions --json` -> 11 ADRs, no errors
- `adr.py index --dir docs/decisions --json` -> 11 ADRs, no warnings
- `adr.py graph --dir docs/decisions --format both --json` -> 6 rendered graph
  edges, no warnings
- `harness-parity` job's Codex and Gemini steps dry-run locally against
  Codex CLI 0.151.0 and Gemini CLI 0.46.0 -- both passed, matching what the
  workflow file runs.

Run the full verification suite again before any further commit, and after
the PR's first real CI run, confirm `harness-parity` actually went green on
GitHub's runners (not just locally) before relying on it as a gate.

## Open risks

- `harness-parity`'s Codex/Gemini steps have only ever run locally on this
  macOS dev machine, never on GitHub's `ubuntu-latest` runners. Watch the
  first real CI run for environment differences (npm registry access,
  network egress rules, `jq` availability -- present by default on
  `ubuntu-latest` but unconfirmed here).
- `adr.py check --uncommitted` reports a `VIOLATED` finding for superseded
  ADR-0003 when changes touch `index.py`; this branch intentionally follows
  ADR-0006, which supersedes ADR-0003. Note that in PR review rather than
  treating it as a code defect.
- CHECK deliberately cannot prove prose, business rationale, or organizational
  claims; those remain human-review evidence.
- Search/relationship matching is deterministic substring/exact/prefix
  matching, untested at real scale. Revisit roadmap scale items if an adopting
  repository reaches hundreds of ADRs.
- GitHub branch/tag protection is intentionally unavailable on the current
  private plan; configure and API-verify after the repository goes public
  (owner has deferred this deliberately, not blocked on it).
