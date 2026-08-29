# handoff.md

Current task:
- Brainstorming (architectural path) for ADR Toolkit MVP, based on
  `adr-toolkit-prd.md` v0.1 draft. Design decisions made in-session with the
  user (index structure, CHECK depth, harness priority, i18n scope) are
  written up in `docs/superpowers/specs/2026-08-29-adr-toolkit-design.md`.

Touched files:
- `docs/superpowers/specs/2026-08-29-adr-toolkit-design.md` (new design doc)
- `project-roadmap.md` (new, holds everything deferred out of MVP)
- `handoff.md` (this file)

Next step:
- Done while user was away: design spec self-reviewed (no placeholders/
  contradictions found), `project-roadmap.md` written, and Plan 1 of 4
  ("core scripts + INIT") written in full to
  `docs/superpowers/plans/2026-08-29-adr-toolkit-core-and-init.md`
  (18 bite-sized TDD tasks, self-reviewed for spec coverage and type
  consistency). All committed locally (no pushes made).
- Deliberately stopped before executing the plan (writing actual
  scripts/*.py code) and before writing Plans 2-4 (RECORD, CHECK,
  i18n+other adapters+release) — that crosses from planning into
  implementation, which per the brainstorming skill's hard gate needs the
  user's explicit go-ahead, and they haven't yet done a line-by-line
  review of the spec itself.
- On the user's return: (1) confirm the MIT license call in spec §13,
  decided in their absence; (2) confirm they're still happy with CHECK's
  structural-only scope (spec §7) now that the concrete rule table exists;
  (3) pick an execution approach for Plan 1 — subagent-driven (fresh
  subagent per task) or inline (executing-plans skill, batched with
  checkpoints); (4) decide whether to write Plans 2-4 now or after Plan 1
  lands.

Open risk:
- CHECK's conflict detection is scoped to structural/path evidence only for
  MVP (semantic taxonomy deferred) — this was an explicit trade discussed
  with the user, not an oversight, but worth re-confirming they're still
  comfortable with it once they see the concrete rule table in §7 of the
  design doc.
- License (MIT) was decided without the user present; must be confirmed,
  not assumed final.
