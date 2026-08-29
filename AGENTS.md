# AGENTS.md

This is the shared operating document for every agent harness working in this
repository (Codex, Claude Code, Gemini, or any other). Harness-specific entry
files (`CODEX.md`, `CLAUDE.md`, `GEMINI.md`) are thin pointers back to this
file — read this one first, regardless of which harness started the session.

## Source of truth

- Canonical source: the code and configuration checked into this repo.
- Generated output: anything produced by build/tooling should be treated as
  disposable and regenerated, not hand-edited.
- Docs: architectural or design context belongs in `docs/` (create it when the
  first doc is written); day-to-day state belongs in `handoff.md`.

## Working flow

- Raw intake: unprocessed input/requests land in the conversation or an issue
  first, not directly as code changes.
- Stable assets: once a decision or design is settled, it should be reflected
  in code and, if non-obvious, in `docs/`.
- Generated files: never hand-edit generated output; change the generator.
- Verification: run the relevant checks (tests, linters, builds) before
  claiming a task is done.

## Handoff

Keep `handoff.md` current with: current task, touched files, next step, and
open risk. Update it whenever a session ends mid-task or context is about to
be lost, so the next session (any harness) can resume without re-deriving
state.

## Improvements

Log recurring problems, deferred work, and automation candidates in
`improvements.md` under `## Open`. Move an item to `## Done` once resolved,
don't delete history.

## Changelog

`changelog.md` is a short, human-readable summary of meaningful changes. It
does not replace `git log` — only note what a human would want to skim
without reading commit-by-commit history.

## Harness entry files

`CODEX.md`, `CLAUDE.md`, and `GEMINI.md` stay thin. They point back to this
file and hold only notes specific to that harness (e.g. a tool quirk). Do not
duplicate rules from this file into them.

## Safety

Do not perform destructive actions (force-push, history rewrite, deleting
branches/files outside the current task, dropping data) without explicit
approval and a confirmed target.

## Verification

Before declaring a task complete, committing, or releasing, run the relevant
verification fresh — do not rely on a stale prior run.
