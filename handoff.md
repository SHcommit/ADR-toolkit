# handoff.md

## Current state (as of 2026-08-30)

Branch: `SHcommit/feat-plan-adr-toolkit`.

- **Plan 1 of 4** (core scripts + INIT/DISCOVER) is complete. It delivered
  the self-contained `skills/adr-toolkit/` package, Claude Code and generic
  harness entry points, deterministic scaffolding/discovery commands, and
  the standalone interactive creation flow.
- **Plan 2 of 4** (RECORD + lifecycle) is implemented across all 11 planned
  tasks. Each task used a fresh implementer/reviewer cycle, with fix rounds
  for body preservation, supersession write-failure guards, behavioral guidance,
  and stronger golden workflow assertions. The current full suite has 105
  passing unit and integration tests.
- Plan 2 delivers deterministic significance scoring, related-ADR search,
  evidence-first RECORD guidance, optional `supersedes`/`superseded_by`
  schema fields, validated `status`/`deprecate`/`supersede` commands, and an
  end-to-end RECORD-to-supersession fixture.
- **Plans 3 and 4** are not yet designed or implemented.

## Exact next action

Design **Plan 3 (CHECK)** from
`docs/superpowers/specs/2026-08-29-adr-toolkit-design.md` sections 7 and 11.
Use the brainstorming skill to confirm the CHECK behavior and boundaries,
then the writing-plans skill to produce the task-by-task implementation plan
under `docs/superpowers/plans/`. Preserve the agreed MVP boundary: CHECK
matches structured `constraints:` evidence only and does not attempt general
semantic conflict detection.

Plan 3 must cover:

1. Parsing the fixed structured constraint vocabulary:
   `forbidden_import`, `required_path`, `forbidden_path`,
   `dependency_forbidden`, `file_must_exist`, and `test_must_exist`.
2. Matching a git diff against Accepted ADRs and their affected paths.
3. Reporting the four finding classes: Related, Review required, Verified
   violation, and No applicable constraint.
4. Presenting all five resolution options for a Verified violation: fix the
   code, supersede the ADR, adjust its scope/constraints, register an
   exception, or mark a false positive.
5. Unit, integration, behavioral, and fixture/golden coverage consistent
   with the deterministic-core and human-approval rules.

After Plan 3, design **Plan 4 (i18n + remaining adapters + release)**. It
covers five-locale runtime text, verified Codex/Gemini CLI/Antigravity CLI
adapter formats, version synchronization, and release automation.

## Open decisions

1. **License:** MIT remains proposed but needs explicit user approval before
   a public release.
2. **Final MVP scope:** confirm whether Plan 4 retains five languages and
   four named harnesses or trims that scope.

## Standing risks

- CHECK's MVP conflict detection is deliberately limited to structural
  evidence from `constraints:` blocks. Full semantic detection remains in
  `project-roadmap.md`; do not expand the MVP boundary without user review.
- Before Plan 4 builds secondary adapters, verify each harness's actual
  manifest/skill format against its documentation. Do not infer those
  formats from the Claude Code adapter.
- Codex `quick_validate.py` rejects the existing cross-harness
  `user-invocable` and `version` skill frontmatter keys. The repository tests
  require those keys today, so resolve validator/metadata compatibility
  deliberately rather than removing them silently.
- `scripts/adr.py` accepts `--json` on every subcommand but always emits JSON;
  decide whether to implement a text mode or remove the ineffective flag.

## Closeout files touched

- `adapters/generic/README.md`
- `improvements.md`
- `changelog.md`
- `handoff.md`
