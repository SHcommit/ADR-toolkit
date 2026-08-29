# project-roadmap.md

Features and improvements that are valuable but deliberately excluded from
the MVP defined in `docs/superpowers/specs/2026-08-29-adr-toolkit-design.md`.
Nothing here is scheduled — it moves into a real design (brainstorming →
spec → plan) only once the MVP has proven the core loop with real usage.

## Conflict detection depth

- Full semantic conflict taxonomy: Direct violation (e.g. SDK called
  directly where a Provider Port was decided) and Pattern divergence
  (diverges from a documented common pattern without touching a named
  path). Needs AST/import-graph analysis beyond MVP's structural,
  path/dependency-based rules.
- Confidence scoring calibrated against a larger golden fixture set once
  real conflicts (and false positives) from actual usage are available.

## Harness parity

- Full cross-harness fixture/golden test matrix for Codex, Gemini CLI, and
  Antigravity CLI, matching the depth Claude Code gets in MVP.
- Harness-specific hook support beyond Claude Code's SessionStart, if the
  other harnesses expose an equivalent trigger.

## ADR navigation and structure

- ADR relationship graph (related/supersedes) rendered as a visual graph,
  not just index list views.
- Investigate whether large decision sets (500+) need anything beyond the
  flat-directory + multi-view-index model chosen for MVP.

## Internationalization

- Localized MADR template section headers (currently English regardless of
  locale).
- Localized project documentation — README, CONTRIBUTING — in the same 5
  languages as the skill's runtime text (en/fr/ja/ko/zh). Wait for real
  non-English/Korean contributors before investing here.

## Ecosystem integration

- Pull request review integration / GitHub App / automated PR comments on
  ADR conflicts.
- ArchUnit-style static enforcement tied to `Implementation Constraints`.
- C4 / arc42 Section 9 export.
- Multi-repo decision graph.
- Vector DB-backed semantic search over ADRs.
- Central decision portal / web viewer.
- Slack / Jira / Notion integrations.

## Open items to revisit once MVP ships

- Whether `retrospective` should become a first-class status instead of
  metadata-only, once enough retrospective ADRs exist to see how they're
  actually used.
- Whether related-ADR search needs more than keyword/tag/affected-path
  matching (e.g. embedding-based similarity) — only worth it once keyword
  search demonstrably misses real cases.
