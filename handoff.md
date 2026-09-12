# handoff.md

## Current task

Resolving GitHub Issues #30 (`Build: PyPA license metadata 현대화`) and #26 (`CI: ruleset required-check drift 자동 검증`). Branch `fix/issue-30-26-build-ci-hardening`.

## Touched files

- `pyproject.toml` — modernized license metadata to SPDX expression (`license = "MIT"`), added `license-files = ["LICENSE*"]`, and removed deprecated license classifier per PEP 639.
- `scripts/verify_rulesets.py` — created script for ruleset required-check drift verification.
- `tests/unit/test_ruleset_drift.py` — added regression test for ruleset drift verification.
- `.github/workflows/test.yml` — added `ruleset-drift` CI job.
- `improvements.md` — moved resolved items to Done.
- `changelog.md` — added notes under `## Unreleased`.
- `handoff.md` — this file.

## Verification

- `scripts/sync_version.py --check`: **exit 0**
- `python -m build`: **exit 0**
- `pytest tests/unit`: **537 passed**
- `git status` / `git diff` clean and verified.

## Next step

1. Complete merge of `origin/develop` into `fix/issue-30-26-build-ci-hardening` and push.
2. Verify PR #50 merge status on GitHub.

## Open risks

- Cline adapter still manually verified; `harness-parity` not covering Cline yet.
- Inherits prior Open risks (ruleset context sync, deferred automation).
