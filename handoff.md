# handoff.md

## Current task

Resolving GitHub Issue #22 (`Release: PyPI publish를 fail-closed로 전환`). Removed `continue-on-error: true` from `.github/workflows/release.yml` to make PyPI publish failures fail-closed.

## Touched files

- `.github/workflows/release.yml` — removed `continue-on-error: true` from `Publish Python Package to PyPI` step.
- `improvements.md` — moved `PyPI publish fail-closed 재검토` from Open to Done.
- `changelog.md` — added note under `## Unreleased`.
- `handoff.md` — this file.

## Verification

- `scripts/sync_version.py --check`: **exit 0**
- `.github/workflows/release.yml` YAML syntax validated via `yaml.safe_load`: **exit 0**
- `git status` / `git diff` clean and verified.

## Next step

1. Commit changes to `fix/issue-22-pypi-fail-closed` branch and push to origin (or PR into `develop`).
2. Close Issue #22 on GitHub (`gh issue close 22 --comment "Fixed via fail-closed release workflow update"`).
3. Proceed to next issue (e.g. Issue #30 PyPA license metadata modernization).

## Open risks

- PyPI publishing failure will now block release workflow completely (intended fail-closed behavior; requires PyPI Trusted Publisher credentials to be fully valid).
- Cline adapter still manually verified; `harness-parity` not covering Cline yet.
- Inherits prior Open risks (ruleset context sync, deferred automation).

## PR #43 pr-title-check stale re-trigger

The first PR #43 title `fix(v1.1.1): ...` did not match the
pr-title-check regex (scope `v1.1.1` contains dots, but the regex allows
only `[a-z0-9-]+`). PR title was retitled to `fix(release): ... for v1.1.1`,
and this follow-up commit re-triggers the workflow so the refresh catches
the new title.
