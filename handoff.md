# handoff.md

## Current task

Resolving GitHub Issues #30 (`Build: PyPA license metadata 현대화`) and #26 (`CI: ruleset required-check drift 자동 검증`). Started on branch `fix/issue-30-26-build-ci-hardening`.

## Touched files

- `handoff.md` — updated for new task focus.

## Verification

- `git status` on branch `fix/issue-30-26-build-ci-hardening`: clean.

## Next step

1. Update `pyproject.toml` to modernize PyPA license metadata to SPDX expression & `license-files` (#30).
2. Implement/verify ruleset required-check drift script / verification (#26).
3. Verify changes (`sync_version.py --check`, pytest, build verification).
4. Commit, push, open PR for `fix/issue-30-26-build-ci-hardening`, and close Issues #30 and #26.

## Open risks

- Cline adapter still manually verified; `harness-parity` not covering Cline yet.
- Inherits prior Open risks (ruleset context sync, deferred automation).
