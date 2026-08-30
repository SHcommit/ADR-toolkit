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
  swallowed rollback failure).
- **Plan 3 of 4** (CHECK) is complete and closed out. Designed via
  brainstorming (resolved in spec §16) and implemented via
  subagent-driven-development across 9 tasks: `core/globs.py` (`**`-aware
  glob matcher), `core/constraints.py` (fenced `constraints:` block
  parser), `commands/diff.py` (git diff wrapper, 3 range modes),
  `rules/conflict.py` (4 structural matching mechanisms the 6 constraint
  kinds collapse into), `commands/check.py` (4-way finding classification:
  Related/Review required/Verified violation/No applicable constraint,
  plus a Superseded-ADR pass), a `references/conflict-rules.md`
  authoring guide, a `SKILL.md` CHECK section, and an end-to-end
  fixture/golden test. One task-level fix round (Task 5, malformed-file
  handling) plus a final whole-branch review that found and fixed 6
  Important issues, including a git argument-injection vulnerability in
  `diff.py`'s `--since` handling that could make the "read-only" CHECK
  command write an arbitrary file (fixed with `--end-of-options`), and
  several "silently reports clean when it actually failed/never
  evaluated" bugs (malformed `affected_paths`, a malformed constraint
  regex, an unknown rule `kind`, a nonexistent ADR directory, and a
  missing-realization heuristic keyed on a heading — "Verification" —
  the toolkit's own templates never produce, since they write
  "Confirmation"). The full suite has 169 passing unit and integration
  tests.
- **Plan 4 of 4** is not yet designed or implemented.

## Next work

- [ ] **Design and implement Plan 4:** add five-locale runtime text, build the
  remaining adapters only after verifying each harness's current format, and
  add version synchronization and release automation.
- [ ] **Resolve release decisions:** obtain explicit approval for the license
  and confirm whether the final MVP retains five languages and four harnesses.
- [ ] **CHECK follow-ups deferred from Plan 3's closeout review:** see
  `project-roadmap.md`'s "CHECK follow-ups" section — a `git ls-files`
  based existing-paths check (perf + `.gitignore` correctness), collapsing
  the `SKIP_FILES`/ADR-loading loop duplicated across 4 command modules
  into a shared helper, documenting that `pattern` syntax differs by rule
  kind, rename handling in `diff.py`, and two narrow `diff.py` edge cases.
  None are blocking; pick up opportunistically or fold into Plan 4.

## Open decisions

Both resolved 2026-08-30:

1. **License:** MIT, confirmed. Plan 4 adds a `LICENSE` file and wires it
   into release automation.
2. **Final MVP scope:** confirmed — Plan 4 keeps the full original scope,
   five languages (en/fr/ja/ko/zh) and four harnesses (Claude Code deep +
   light adapters for Codex/Gemini CLI/Antigravity CLI), per spec §2/§8/§9.

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

## Closeout files touched (Plan 3)

- `skills/adr-toolkit/scripts/core/globs.py`
- `skills/adr-toolkit/scripts/core/constraints.py`
- `skills/adr-toolkit/scripts/commands/diff.py`
- `skills/adr-toolkit/scripts/commands/check.py`
- `skills/adr-toolkit/scripts/rules/conflict.py`
- `skills/adr-toolkit/scripts/adr.py`
- `skills/adr-toolkit/references/conflict-rules.md`
- `skills/adr-toolkit/SKILL.md`
- `docs/superpowers/specs/2026-08-29-adr-toolkit-design.md`
- `docs/superpowers/plans/2026-08-30-adr-toolkit-check.md`
- `tests/unit/test_globs.py`, `test_constraints.py`, `test_diff.py`,
  `test_conflict.py`, `test_check.py`, `test_conflict_rules_reference.py`,
  `test_skill_manifest.py`
- `tests/fixtures/check_provider_port/`, `tests/integration/test_check_workflow.py`
- `project-roadmap.md`
- `improvements.md`
- `changelog.md`
- `handoff.md`
