# handoff.md

## Current state (as of 2026-08-30)

Branch: `SHcommit/feat-plan-adr-toolkit`. **All 4 plans of the ADR Toolkit
MVP are complete and closed out on this branch.** Master still holds only
the initial commit — integrating this branch (merge locally, open a PR, or
keep as-is) is now a live decision for the user, not a deferred one; do
not merge or push without asking first.

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
  "Confirmation").
- **Plan 4 of 4** (i18n, adapters, release automation) is complete and
  closed out. Designed via brainstorming (resolved in spec §17) and
  implemented via subagent-driven-development across 8 tasks:
  `core/locale.py` + 5 locale JSON files (en/fr/ja/ko/zh, scoped to only
  `index.py`'s generated strings — everything else stays agent-composed
  prose per a new `SKILL.md` Language instruction), `index.py --locale`
  wiring, and three new harness adapters (`adapters/codex/`,
  `adapters/gemini-cli/`, `adapters/antigravity/`), each with a
  symlink-based install README (no symlink committed to git). Real
  manual end-to-end verification was performed for Codex and Gemini
  (both CLIs installed in this dev environment) — Codex needed two
  correction rounds (a task-level fix disclosing an initial false
  "Codex CLI can't do this" claim, then a final-review fix correcting
  the documented install path to match spec §17.2 and re-verifying via
  `codex plugin marketplace add`/`plugin add` against this repo's
  existing `.claude-plugin/marketplace.json`, which works); Gemini's
  worked cleanly and was independently reproduced twice by reviewers;
  Antigravity has no CLI available here, so it's structural-only,
  stated plainly. Also added `scripts/sync_version.py` (repo-root
  tooling, outside the distributable package) plus CI wiring and a
  tag-triggered `release.yml`. A final whole-branch review found and
  fixed 1 Critical (the Codex README's wrong path + false claim) and 6
  Important issues (`release.yml` missing write permissions, a release
  step that never actually checked the pushed tag against `VERSION`,
  `index --locale` hard-crashing on a malformed/missing locale file,
  `.gitignore` not covering the adapter symlink paths its own READMEs
  instruct users to create, `sync_version.py` not validating `VERSION`'s
  content, and `sync_version.py` silently skipping a missing manifest
  with no test coverage of its real file paths).
- **Full suite: 212 passing unit and integration tests.**

## Next work

- [ ] **Decide how to integrate this branch.** Options: merge to master
  locally, push and open a PR, or keep as-is for now. The full 4-plan MVP
  is done, so this is no longer blocked — it's the next decision.
- [ ] **CHECK follow-ups deferred from Plan 3's closeout review:** see
  `project-roadmap.md`'s "CHECK follow-ups" section — a `git ls-files`
  based existing-paths check (perf + `.gitignore` correctness), collapsing
  the `SKIP_FILES`/ADR-loading loop duplicated across 4 command modules
  into a shared helper, documenting that `pattern` syntax differs by rule
  kind, rename handling in `diff.py`, and two narrow `diff.py` edge cases.
- [ ] **i18n/adapter/release follow-ups deferred from Plan 4's closeout
  review:** see `project-roadmap.md`'s "i18n, adapters, release
  follow-ups" section. None are blocking.

## Open decisions

Resolved 2026-08-30:

1. **License:** MIT, confirmed. `LICENSE` already exists at repo root
   (from the initial commit) and is wired into `release.yml`.
2. **Final MVP scope:** confirmed — Plan 4 kept the full original scope,
   five languages (en/fr/ja/ko/zh) and four harnesses (Claude Code deep +
   light adapters for Codex/Gemini CLI/Antigravity CLI), per spec §2/§8/§9.

No open decisions remain from the original design spec. The one live
decision now is branch integration (see Next work above).

## Standing risks

- CHECK's MVP conflict detection is deliberately limited to structural
  evidence from `constraints:` blocks. Full semantic detection remains in
  `project-roadmap.md`; do not expand the MVP boundary without user review.
- Codex `quick_validate.py` rejects the existing cross-harness
  `user-invocable` and `version` skill frontmatter keys. The repository tests
  require those keys today, so resolve validator/metadata compatibility
  deliberately rather than removing them silently.
- `scripts/adr.py` accepts `--json` on every subcommand but always emits JSON;
  deliberately left untouched by Plan 4 (§17.1) — decide whether to
  implement a text mode or remove the ineffective flag.
- The Codex adapter's documented install path only exercises this repo's
  root-level `.claude-plugin/marketplace.json` — the `.codex-plugin/`
  manifest and its sibling `skills/` symlink (mandated by spec §17.2) are
  present and correctly laid out, but Codex's own `plugin marketplace add`
  never actually reads them in the verified flow (it reads the repo-root
  marketplace file instead). Worth a follow-up once Codex's Agent Plugins
  1.0.0 support matures — see `project-roadmap.md`.

## Closeout files touched (Plan 4)

- `skills/adr-toolkit/scripts/core/locale.py`
- `skills/adr-toolkit/scripts/i18n/{en,fr,ja,ko,zh}.json`
- `skills/adr-toolkit/scripts/commands/index.py`
- `skills/adr-toolkit/scripts/adr.py`
- `skills/adr-toolkit/SKILL.md`
- `adapters/codex/`, `adapters/gemini-cli/`, `adapters/antigravity/`
- `scripts/sync_version.py`
- `.github/workflows/test.yml`, `.github/workflows/release.yml`
- `.gitignore`
- `docs/superpowers/specs/2026-08-29-adr-toolkit-design.md`
- `docs/superpowers/plans/2026-08-30-adr-toolkit-i18n-adapters-release.md`
- `tests/unit/test_locale.py`, `test_codex_adapter.py`,
  `test_gemini_cli_adapter.py`, `test_antigravity_adapter.py`,
  `test_sync_version.py`, `test_adr_cli.py` (new); `test_index.py`,
  `test_skill_manifest.py` (extended)
- `project-roadmap.md`
- `improvements.md`
- `changelog.md`
- `handoff.md`
