# handoff.md

## Current task

Resolving GitHub Issue #23 (`Automation: 규모 trigger 기반 자동화`). Branch `feature/issue-23-automation-triggers`.

## Touched files

- `.github/workflows/stale.yml` — created scale-triggered automated stale issue and PR lifecycle workflow.
Resolving GitHub Issue #28 (`Test: harness parity를 check/search/graph/create까지 확장`). Branch `feature/issue-28-harness-parity-expansion`.

## Touched files

- `.github/workflows/test.yml` — expanded `harness-parity` CI job to verify `create`, `search`, `graph`, and `check` commands across Codex, Antigravity, and Gemini CLI adapters.
Resolving GitHub Issues #33 (`Docs: adapters/README.md tutorial`) and #29 (`Docs: Accepted ADR metadata factual-correction policy`). Branch `docs/issue-33-29-docs-and-policy`.

## Touched files

- `adapters/README.md` — added overview table and step-by-step tutorial for adding new harness adapters.
- `docs/factual-correction-policy.md` — defined permitted in-place metadata edits vs prohibited decision changes for Accepted ADRs.
- `improvements.md` — moved resolved items to Done.
- `changelog.md` — added notes under `## Unreleased`.
- `handoff.md` — this file.

## Verification

- `scripts/sync_version.py --check`: **exit 0**
- `.github/workflows/stale.yml` YAML syntax validated: **exit 0**
- `.github/workflows/test.yml` YAML syntax validated: **exit 0**
- `git status` clean and verified.

## Next step

1. Complete merge of `origin/develop` into `feature/issue-23-automation-triggers` and push.
2. Verify PR #53 merge status on GitHub.
1. Complete merge of `origin/develop` into `feature/issue-28-harness-parity-expansion` and push.
2. Verify PR #52 merge status on GitHub.
1. Merge PR #51 into `develop`.
2. Proceed to PR #52 and PR #53 merges.

## Open risks

- Cline adapter still manually verified; `harness-parity` not covering Cline yet.
- Inherits prior Open risks (ruleset context sync, deferred automation).
