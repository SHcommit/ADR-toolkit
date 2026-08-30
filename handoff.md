# handoff.md

## Current task (2026-08-30)

ADR Toolkit `v0.2.0` minor-release implementation and local release evidence
are complete: repository-configured eight-locale ADR generation, portable
multilingual filenames, CHECK false-confidence fixes, dogfooded ADR quality
corrections, user documentation, and separate Korean readiness/enterprise
reports.

The work runs in the linked worktree `develop-2`. Its base is the current
`origin/develop` history plus the approved design commits:

- `7b9bb8c` — initial localization/readiness design
- `b69a784` — v0.2.0 release gates, repository config, CHECK confidence, and
  report separation

Baseline verification before implementation: `212 passed` on 2026-08-30.

Latest local release evidence on 2026-08-30:

- `python3 -m pytest -q` → `290 passed`, exit 0
- `python3 scripts/sync_version.py --check` → exit 0
- repository validation → 6 ADRs, no errors
- regenerated decision index → byte-identical

The detailed evidence and maturity assessment are in
`docs/adr-toolkit-v0.2.0-readiness-report.md`; post-release governance is kept
separate in `docs/enterprise-adoption.md`.

## Next step

Commit the final reports and tracking reconciliation, then open the final PR.
After required CI passes, obtain explicit approval for the v0.2.0 version bump,
release branch, push, and tag. Until then the readiness decision is conditional
GO and tag release is NO-GO.

## Open risks

- Catalog structure is deterministic, but terminology still benefits from
  native-speaker review in each supported language.
- CHECK deliberately cannot prove prose, business rationale, or organizational
  claims; those remain human-review evidence.
- GitHub protection is intentionally unavailable in the current private plan;
  configure and API-verify it after the repository becomes public.
- Version bump, release branch, push, and tag are not authorized by this task.
