# improvements.md

Backlog for follow-up improvements that are useful but not required to resume
the current session.

## Open

- `adapters/generic/README.md` line 29 has a leftover bare
  `python scripts/adr.py` reference in prose; should match the rest of the
  file's `python skills/adr-toolkit/scripts/adr.py` form. Found by the
  final whole-branch review on Plan 1, judged non-blocking at the time.
- `scripts/adr.py`'s `--json` flag is parsed on every subcommand but never
  read (output is always JSON regardless). Either implement a non-JSON
  mode or drop the flag.
- `core/schema.py` (the enforced validator) and `schemas/adr.schema.json`
  (the human/tool-readable reference) are hand-synced by design with no
  test asserting they agree — they will silently drift as fields are added
  in later plans.
- Confirm with the user whether the final MVP keeps 5 languages / 4
  harnesses as originally agreed, or trims further — raised once in
  conversation, not yet answered. Doesn't block Plan 1 (English + Claude
  Code only), but affects Plan 4's scope.
- Before building the Codex/Gemini CLI/Antigravity CLI adapters (Plan 4),
  verify each harness's real plugin/skill manifest format against actual
  documentation. The original Claude Code adapter guessed a `"skills"` key
  and a nested manifest path that turned out not to match real Claude Code
  plugins (caught by final review, fixed to a repo-root
  `.claude-plugin/plugin.json` with no `"skills"` key, relying on
  auto-discovery) — don't repeat that mistake for the other three.

## Done

- Bootstrapped shared harness operating files (`AGENTS.md`, thin
  `CLAUDE.md`/`CODEX.md`/`GEMINI.md`, `handoff.md`/`improvements.md`/
  `changelog.md`) so any harness starting cold defers to the same rules.
- ADR Toolkit MVP design spec written and iterated
  (`docs/superpowers/specs/2026-08-29-adr-toolkit-design.md`), covering
  repo structure, ADR document format (incl. structured `constraints:`
  blocks and the retrospective Confirmed Evidence/Inferred
  Rationale/Unknown split), CHECK's structural-only MVP scope, harness
  strategy (Claude Code deep + generic fallback + light adapters),
  i18n scope, and the INIT/DISCOVER operation split.
- `project-roadmap.md` created to hold everything explicitly deferred out
  of MVP.
- Plan 1 of 4 ("core scripts + INIT/DISCOVER") designed
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
