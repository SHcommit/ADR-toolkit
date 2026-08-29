# handoff.md

## Current state (as of 2026-08-30)

Branch `SHcommit/feat-plan-adr-toolkit` (off `master`), pushed to `origin`,
working tree clean.

- **Plan 1 of 4** ("core scripts + INIT/DISCOVER") — DONE. Implemented via
  subagent-driven-development, 20 tasks + a final-review fix wave, all
  clean. 73/73 tests passing. Delivers a self-contained
  `skills/adr-toolkit/` package usable via Claude Code, any other harness
  (generic manifest-free fallback), or no AI agent at all (`create
  --interactive`).
- **Plan 2 of 4** ("RECORD + lifecycle") — **DESIGNED, NOT EXECUTED.**
  Full plan document written and committed:
  `docs/superpowers/plans/2026-08-30-adr-toolkit-record-and-lifecycle.md`
  (11 bite-sized TDD tasks, each with exact test code + exact
  implementation code already written out — nothing left to design,
  only to execute). Not run due to a token-budget constraint in the
  session that wrote it.
- **Plans 3 and 4** — not yet designed at all.

## Exact next action — resume here, no re-derivation needed

Run this single command to execute Plan 2 exactly as Plan 1 was executed:

```
Use superpowers:subagent-driven-development to execute
docs/superpowers/plans/2026-08-30-adr-toolkit-record-and-lifecycle.md
task by task (fresh implementer + fresh reviewer per task, final
whole-branch review at the end). Spec:
docs/superpowers/specs/2026-08-29-adr-toolkit-design.md.
```

What this will do, task by task (all already fully specified in the plan
file — this list is just so you don't have to open it to know the shape):

1. `core/identifiers.find_by_number` — locate an ADR file by numeric ID
2. `rules/significance.py` — deterministic 0–14 scoring/banding
3. `commands/significance.py` + wire into `adr.py`
4. `commands/related.py` (search by path/tag/keyword) + wire into `adr.py`
5. Extend `core/schema.py` with optional `supersedes`/`superseded_by`
6. `commands/status.py` (validated transition) + `deprecate` alias in `adr.py`
7. `commands/supersede.py` (bidirectional link update)
8. `references/significance-rules.md`
9. `references/interview-guide.md`
10. `SKILL.md` — add `## RECORD` and `## Lifecycle operations` sections
11. End-to-end RECORD/supersede fixture + golden test

Expect this to look like Plan 1's execution: ~11 implementer dispatches,
~11 task reviews, occasional fix-loop rounds if a reviewer finds something,
then one final whole-branch review + at most one fix wave + one scoped
re-review, then the finishing-a-development-branch skill's menu again
(merge / PR / keep-as-is).

## After Plan 2 lands

- **Plan 3 (CHECK)** — not yet written. When ready, brainstorm/plan it
  from spec §7 (structured `constraints:` YAML rule matching, four-way
  finding classification: Related / Review required / Verified violation /
  No applicable constraint, five resolution options on a verified
  violation) and spec §11's CHECK data-flow section.
- **Plan 4 (i18n + remaining adapters + release)** — not yet written.
  Covers: 5-locale i18n wiring into the skill's runtime text (spec §9);
  Codex/Gemini CLI/Antigravity CLI adapters — **verify each harness's real
  plugin/skill manifest format against actual documentation before
  building these**, do not assume it mirrors Claude Code (the original
  Claude adapter guessed wrong — a `"skills"` key and nested manifest path
  that don't match real Claude Code plugins — caught only by Plan 1's
  final review and fixed to a repo-root `.claude-plugin/plugin.json` with
  no `"skills"` key, relying on auto-discovery); release automation
  (version sync across `skills/adr-toolkit/VERSION`/`.claude-plugin/
  plugin.json`, CHANGELOG, GitHub Release).

## Open decisions still unresolved (don't block Plan 2, do block a public 1.0)

1. **License** — MIT was proposed in the design spec (§13) while the user
   was away from the keyboard. Needs explicit sign-off before any public
   release; not yet confirmed.
2. **Final MVP scope** — whether to keep 5 languages / 4 harnesses as
   originally agreed in conversation, or trim further. Raised once, never
   answered. Plan 1 is unaffected either way (it only built English +
   Claude Code); this only matters for Plan 4's actual scope.
3. **Trivial doc fix** — `adapters/generic/README.md` line 29 still has a
   bare `python scripts/adr.py` reference in prose; every other invocation
   in that file correctly says `python skills/adr-toolkit/scripts/adr.py`.
   Found by Plan 1's final review, judged non-blocking, still unfixed.
   One-line fix whenever someone is next in that file.

## Standing risks worth remembering

- CHECK's conflict detection is deliberately scoped to structural/
  `constraints:`-block evidence only for MVP (the PRD's full semantic
  taxonomy — Direct violation, Pattern divergence — is deferred to
  `project-roadmap.md`). This was an explicit trade agreed with the user,
  not an oversight — don't "fix" it into semantic analysis without
  checking with them first.
- `core/schema.py` (the enforced validator) and `schemas/adr.schema.json`
  (the human/tool-readable reference) are hand-synced by design with no
  test asserting they agree. Plan 2's Task 5 adds fields to `schema.py`
  only — remember to update `adr.schema.json` too if anyone ever adds that
  sync test (tracked in `improvements.md`, not yet done).
