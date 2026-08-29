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
- User is away (~30 min, granted permission to proceed without asking).
  Self-review of the design doc is done inline (no placeholders, no
  contradictions found). Proceeding to invoke the writing-plans skill to
  turn the spec into an implementation plan.
- On the user's return: get explicit sign-off on the spec (especially the
  MIT license call made in §13 of the design doc, which was decided
  in-absence and needs confirmation before any public release) before
  starting actual code implementation.

Open risk:
- CHECK's conflict detection is scoped to structural/path evidence only for
  MVP (semantic taxonomy deferred) — this was an explicit trade discussed
  with the user, not an oversight, but worth re-confirming they're still
  comfortable with it once they see the concrete rule table in §7 of the
  design doc.
- License (MIT) was decided without the user present; must be confirmed,
  not assumed final.
