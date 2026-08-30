# handoff.md

## Current state (as of 2026-08-30)

The full 4-plan ADR Toolkit MVP is complete and pushed to `origin` on
branch `feat/adr-toolkit-mvp-implement` (renamed from
`SHcommit/feat-plan-adr-toolkit`; the old name still exists as a stale
remote branch that was never deleted). Not yet merged to `master`, no PR
open — see `improvements.md`'s `## Open` list for what's pending.

For what shipped, see `changelog.md`. For deferred/follow-up work, see
`improvements.md` and `project-roadmap.md` — this file no longer repeats
that history; keeping it in three places was how it drifted.

## Standing risks

- Codex `quick_validate.py` rejects the existing cross-harness
  `user-invocable` and `version` skill frontmatter keys. The repository
  tests require those keys today; resolve validator/metadata
  compatibility deliberately rather than removing them silently.
- `scripts/adr.py` accepts `--json` on every subcommand but always emits
  JSON; deliberately left untouched by Plan 4 (design spec §17.1).
- The Codex adapter's documented install path only exercises this repo's
  root-level `.claude-plugin/marketplace.json` — the `.codex-plugin/`
  manifest and its sibling `skills/` symlink (spec §17.2) are present and
  correctly laid out but not exercised by Codex's own `plugin marketplace
  add` in the verified flow. Revisit once Codex's Agent Plugins 1.0.0
  support matures.
