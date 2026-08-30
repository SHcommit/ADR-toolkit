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

- [x] Closed out Plan 4 (i18n, adapters, release automation) — the final
  plan of the 4-plan MVP: all 8 tasks implemented via
  subagent-driven-development, task-reviewed clean (one fix round on
  Task 4's Codex adapter, disclosing an initial false "Codex CLI can't do
  this" claim), plus a final whole-branch review that found and fixed 1
  Critical and 6 Important issues in one fix wave — the Codex README's
  documented install path was wrong (nested `skills/` instead of a spec
  §17.2 sibling) and its "Codex is the gap" claim was false (re-verified:
  `codex plugin marketplace add`/`plugin add` against this repo's own
  `.claude-plugin/marketplace.json` actually works); `release.yml` was
  missing `permissions: contents: write` (would likely 403 on the first
  real tag) and never actually checked the pushed tag against `VERSION`;
  `index --locale` hard-crashed on a malformed/missing locale file,
  violating the spec's explicit "never a crash" rule; `.gitignore` didn't
  cover the adapter symlink paths its own READMEs instruct users to
  create; and `sync_version.py` neither validated `VERSION`'s content
  (empty/multiline/regex-template-injection risk) nor caught a silently
  missing real manifest. Full suite: 212/212 passing (up from 193 at task
  completion, 169 before Plan 4). **The full 4-plan ADR Toolkit MVP is
  now complete.**
- [x] Closed out Plan 3 (CHECK): all 9 tasks implemented via
  subagent-driven-development, task-reviewed clean (one fix round on
  Task 5's malformed-file handling), plus a final whole-branch review
  that found and fixed 6 Important issues in one fix wave — a git
  argument-injection vulnerability in `diff.py`'s `--since` handling
  (could make the "read-only" CHECK command write an arbitrary file, now
  closed with `--end-of-options`), and five "silently reports clean
  instead of erroring/warning" bugs across `affected_paths` handling,
  constraint-regex compilation, unknown rule kinds, a nonexistent ADR
  directory, and a missing-realization heuristic keyed on a heading the
  toolkit's own templates never produce. Full suite: 169/169 passing (up
  from 154 at task completion, 114 baseline before Plan 3).
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
