# handoff.md

## Current task

Resolving GitHub Issues #33 (`Docs: adapters/README.md tutorial`) and #29 (`Docs: Accepted ADR metadata factual-correction policy`). Branch `docs/issue-33-29-docs-and-policy`.

## Touched files

- `adapters/README.md` — added overview table and step-by-step tutorial for adding new harness adapters.
- `docs/factual-correction-policy.md` — defined permitted in-place metadata edits vs prohibited decision changes for Accepted ADRs.
- `improvements.md` — moved resolved items to Done.
- `changelog.md` — added notes under `## Unreleased`.
- `handoff.md` — this file.

## Verification

- `scripts/sync_version.py --check`: **exit 0**
- `git status` clean and verified.

## Next step

1. Complete merge of `origin/develop` into `docs/issue-33-29-docs-and-policy` and push.
2. Verify PR #51 merge status on GitHub.

## Open risks

- Cline adapter still manually verified; `harness-parity` not covering Cline yet.
- Inherits prior Open risks (ruleset context sync, deferred automation).
