# changelog.md

Lightweight human-readable summary of meaningful repository changes.

## Unreleased

- Added the RECORD workflow: deterministic significance scoring, related-ADR
  search, evidence-first interviewing guidance, MADR drafting rules, and an
  end-to-end RECORD fixture.
- Added validated ADR lifecycle commands for status changes, deprecation,
  and bidirectional supersession, including dry-run and partial-write
  safeguards.
- Added optional relationship fields to runtime and JSON Schema validation,
  with parity coverage to prevent schema drift.
- Closed out Plan 2 with a final whole-branch review: hardened `related`,
  `significance`, `status`, and `supersede` against malformed input
  (bad frontmatter, non-list fields, missing IDs, bad JSON) and added a
  supersede invariant requiring the superseding ADR to already be
  `accepted`.
- Added the CHECK workflow: `diff`/`check` CLI commands, a `**`-aware glob
  matcher, a `constraints:` block parser, and a 4-way finding
  classification (Related/Review required/Verified violation/No applicable
  constraint) matching a git diff against Accepted ADRs' structural
  constraint rules and Superseded ADRs' affected paths. Closed out with a
  final whole-branch review that fixed a git argument-injection
  vulnerability and several "silently reports clean" gaps.
