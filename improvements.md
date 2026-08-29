# improvements.md

Backlog for follow-up improvements that are useful but not required to resume
the current session.

## Open

- [ ] `scripts/adr.py`'s `--json` flag is parsed on every subcommand but never
  read (output is always JSON regardless). Either implement a non-JSON
  mode or drop the flag.
- [ ] Codex's `quick_validate.py` rejects the existing ADR Toolkit `SKILL.md`
  frontmatter keys `user-invocable` and `version`, while the repository's
  cross-harness contract and tests currently require them. Make a deliberate
  metadata/validator compatibility decision before changing either side;
  do not silently delete the keys to satisfy one harness.
- [ ] Confirm with the user whether the final MVP keeps 5 languages / 4
  harnesses as originally agreed, or trims further — raised once in
  conversation, not yet answered. Doesn't block Plan 1 (English + Claude
  Code only), but affects Plan 4's scope.
- [ ] Before building the Codex/Gemini CLI/Antigravity CLI adapters (Plan 4),
  verify each harness's real plugin/skill manifest format against actual
  documentation. The original Claude Code adapter guessed a `"skills"` key
  and a nested manifest path that turned out not to match real Claude Code
  plugins (caught by final review, fixed to a repo-root
  `.claude-plugin/plugin.json` with no `"skills"` key, relying on
  auto-discovery) — don't repeat that mistake for the other three.

## Done

- [x] Closed out Plan 2: final whole-branch review of `37067b1..HEAD` found
  six confirmed robustness gaps (malformed frontmatter aborting `related`
  instead of degrading like `validate`/`index`; `significance`/`status`
  missing the specific-error-code handling `create`/`validate` already use;
  `supersede` not validating the superseding ADR's own status or guarding
  missing IDs; a swallowed second failure in `supersede`'s rollback path).
  Fixed all six in one wave with regression tests. Full suite: 114/114
  passing (up from 105).
- [x] Completed Plan 2 of 4 (RECORD + lifecycle): all 11 tasks are implemented
  and task-reviewed, lifecycle defects found during review are fixed, and the
  full unit/integration suite passes 105 tests.
- [x] Corrected the stale bare `python scripts/adr.py` invocation in
  `adapters/generic/README.md` to the documented generic install location,
  `python .agents/skills/adr-toolkit/scripts/adr.py`.
- [x] Kept runtime ADR validation and the published JSON Schema in sync when
  Plan 2 added `supersedes` and `superseded_by`, and added a unit parity
  test so future field changes cannot silently drift between
  `core/schema.py` and `schemas/adr.schema.json`.
- [x] Bootstrapped shared harness operating files (`AGENTS.md`, thin
  `CLAUDE.md`/`CODEX.md`/`GEMINI.md`, `handoff.md`/`improvements.md`/
  `changelog.md`) so any harness starting cold defers to the same rules.
- [x] ADR Toolkit MVP design spec written and iterated
  (`docs/superpowers/specs/2026-08-29-adr-toolkit-design.md`), covering
  repo structure, ADR document format (incl. structured `constraints:`
  blocks and the retrospective Confirmed Evidence/Inferred
  Rationale/Unknown split), CHECK's structural-only MVP scope, harness
  strategy (Claude Code deep + generic fallback + light adapters),
  i18n scope, and the INIT/DISCOVER operation split.
- [x] `project-roadmap.md` created to hold everything explicitly deferred out
  of MVP.
- [x] Plan 1 of 4 ("core scripts + INIT/DISCOVER") designed
  (`docs/superpowers/plans/2026-08-29-adr-toolkit-core-and-init.md`, 20
  tasks) and fully implemented via subagent-driven-development: every task
  built and reviewed clean (one fix loop on Task 11's dry-run/id bugs), a
  final whole-branch review found and a single fix wave resolved 2
  Critical + 3 Important issues (CI missing a pytest install step, an
  empty-slug bug that could reuse ADR IDs, a wrong Claude Code adapter
  manifest layout, wrong script invocation paths in `SKILL.md`, and
  uncaught exceptions breaking the JSON-only-stdout contract), scoped
  re-review confirmed all addressed with no new breakage. 73/73 tests
  passing. Delivers: a self-contained `skills/adr-toolkit/` package usable
  three ways (Claude Code, a generic manifest-free fallback for any other
  harness, and a no-agent `create --interactive` terminal wizard).
