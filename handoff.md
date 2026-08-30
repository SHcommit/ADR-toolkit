# handoff.md

## Current task (2026-08-30)

Prepare ADR Toolkit `v0.2.0` as a minor feature release: repository-configured
eight-locale ADR generation, portable multilingual filenames, CHECK
false-confidence fixes, dogfooded ADR quality corrections, and separate Korean
readiness/enterprise-adoption reports.

The work runs in the linked worktree `develop-2`. Its base is the current
`origin/develop` history plus the approved design commits:

- `7b9bb8c` — initial localization/readiness design
- `b69a784` — v0.2.0 release gates, repository config, CHECK confidence, and
  report separation

Baseline verification before implementation: `212 passed` on 2026-08-30.

## Touched files

- `docs/superpowers/specs/2026-08-30-adr-toolkit-localization-and-readiness-design.md`
- `handoff.md`
- `improvements.md`
- `project-roadmap.md`

Local execution plans live under ignored `docs/superpowers/plans/`.

## Next step

Implement `.adr-toolkit.json`, locale resolution, eight catalogs, localized
rendering, and semantic-slug validation with TDD. Then harden CHECK, correct the
existing ADRs, request the lifecycle checkpoint for ADR-0003 supersession, and
finish reports/documentation.

## Open risks

- Locale precedence must distinguish an omitted CLI flag from explicit English.
- Translation catalogs need exact key parity and human-readable terminology.
- ADR-0003's MVP decision is replaced by v0.2.0 and must be superseded through
  the lifecycle command, not silently rewritten.
- Known CHECK rename/path/subprocess defects can produce false confidence until
  fixed and regression-tested.
- GitHub protection is intentionally unavailable in the current private plan;
  configure and API-verify it after the repository becomes public.
- Version bump, release branch, push, and tag are not authorized by this task.
