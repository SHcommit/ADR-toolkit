# handoff.md

## Current state (as of 2026-08-30)

Branch: `SHcommit/feat-plan-adr-toolkit`. Master holds only the initial
commit — all Plan 1-4 work accumulates on this one branch and merges to
master only once the full MVP (all 4 plans) is done; do not open a PR for
a partial plan without asking first.

- **Plan 1 of 4** (core scripts + INIT/DISCOVER) is complete. It delivered
  the self-contained `skills/adr-toolkit/` package, Claude Code and generic
  harness entry points, deterministic scaffolding/discovery commands, and
  the standalone interactive creation flow.
- **Plan 2 of 4** (RECORD + lifecycle) is complete and closed out. All 11
  planned tasks were implemented with a fresh implementer/reviewer cycle
  each, plus a final whole-branch review (`37067b1..HEAD`) that found and
  fixed six confirmed robustness gaps in `related`/`significance`/`status`/
  `supersede` (malformed-frontmatter handling, specific error codes for bad
  input files, a missing supersede-status invariant, and a silently
  swallowed rollback failure). The full suite has 114 passing unit and
  integration tests.
- Plan 2 delivers deterministic significance scoring, related-ADR search,
  evidence-first RECORD guidance, optional `supersedes`/`superseded_by`
  schema fields, validated `status`/`deprecate`/`supersede` commands, and an
  end-to-end RECORD-to-supersession fixture.
- **Plans 3 and 4** are not yet designed or implemented.

## Next work

- [ ] **Design Plan 3 (CHECK):** use the brainstorming skill against
  `docs/superpowers/specs/2026-08-29-adr-toolkit-design.md` sections 7 and 11,
  then use the writing-plans skill to create the task-by-task plan under
  `docs/superpowers/plans/`.
- [ ] **Implement Plan 3:** execute the approved plan with TDD, task reviews,
  a final whole-branch review, and fixture/golden coverage.
- [ ] **Design and implement Plan 4:** add five-locale runtime text, build the
  remaining adapters only after verifying each harness's current format, and
  add version synchronization and release automation.
- [ ] **Resolve release decisions:** obtain explicit approval for the license
  and confirm whether the final MVP retains five languages and four harnesses.

Plan 3 must preserve the agreed MVP boundary: CHECK matches structured
`constraints:` evidence only and does not attempt general semantic conflict
detection. Its implementation plan must cover:

1. Parsing `forbidden_import`, `required_path`, `forbidden_path`,
   `dependency_forbidden`, `file_must_exist`, and `test_must_exist`.
2. Matching a git diff against Accepted ADRs and their affected paths.
3. Reporting Related, Review required, Verified violation, and No applicable
   constraint findings.
4. Presenting all five Verified violation resolutions: fix the code,
   supersede the ADR, adjust its scope/constraints, register an exception,
   or mark a false positive.
5. Unit, integration, behavioral, and fixture/golden coverage consistent
   with the deterministic-core and human-approval rules.

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

- `skills/adr-toolkit/scripts/commands/related.py`
- `skills/adr-toolkit/scripts/commands/significance.py`
- `skills/adr-toolkit/scripts/commands/status.py`
- `skills/adr-toolkit/scripts/commands/supersede.py`
- `skills/adr-toolkit/references/lifecycle.md`
- `tests/unit/test_related.py`
- `tests/unit/test_significance_command.py`
- `tests/unit/test_status.py`
- `tests/unit/test_supersede.py`
- `improvements.md`
- `changelog.md`
- `handoff.md`
