# changelog.md

Lightweight human-readable summary of meaningful repository changes.

## Unreleased

- Added repository-configured deterministic ADR localization for eight locales
  (`en`, `ko`, `ja`, `zh`, `fr`, `es`, `de`, `pt-BR`) across INIT, CREATE,
  templates, prompts, and INDEX, with strict config/schema validation and
  explicit override precedence.
- Added portable multilingual ADR creation: Unicode titles and bodies are
  preserved, an approved semantic ASCII slug can be supplied, and non-ASCII
  titles safely fall back to an ID-qualified `decision` filename.
- Hardened CHECK against false-clean results by failing closed on incomplete git
  evidence, retaining both sides of renames and Unicode paths, detecting
  working-tree deletions, exposing invalid ADRs, following Git ignore/path
  semantics, and rejecting conflicting diff modes.
- Made relative ADR directories resolve consistently from `--root` for every
  repository-scoped generation and validation command.
- Improved the repository's own ADR evidence and lifecycle history, including
  the accepted ADR-0006 decision that supersedes the MVP index-only
  localization decision ADR-0003.
- Expanded README, quickstart, and skill guidance with real multilingual
  workflows and CHECK confidence boundaries, and added separate Korean v0.2.0
  readiness and enterprise-adoption reports.
- Added the self-contained `skills/adr-toolkit/` package: deterministic
  scaffolding/discovery commands (`init`, `discover`, `preflight`,
  `validate`, `index`), ADR frontmatter/ID/lifecycle core logic, MADR
  templates, and a no-agent `create --interactive` terminal wizard. Usable
  three ways: Claude Code (deep integration), a generic manifest-free
  fallback for any other harness, or standalone from the terminal. CI
  (matrix-tested pytest) built in from the first commit.
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
- Added five-language i18n for `index`'s generated `README.md`
  (`--locale en|fr|ja|ko|zh`), light adapters for Codex CLI, Gemini CLI,
  and Antigravity CLI (manifest formats verified against real
  documentation, not guessed), a repo-root version-sync script, and a
  tag-triggered release workflow. This closes out Plan 4 of 4 — the full
  ADR Toolkit MVP is now complete on this branch.
- Released v0.1.0 and adopted a Git Flow branch policy
  (`develop`/`master`/`feature`/`release`/`hotfix`, direct-tag release
  automation), recorded in `AGENTS.md`.
- Dogfooded the toolkit on its own repo: initialized `docs/decisions/`
  and recorded the four most significant architectural decisions made
  while building it (CHECK's structural-only scope, i18n's index-only
  scope, adapter packaging policy, the Git Flow adoption itself).
- Wrote the root `README.md` (previously a one-line stub) and
  `examples/quickstart.md`, a full INIT → RECORD → CHECK walkthrough with
  real command output, including CHECK catching a live rule violation and
  clearing it after a fix.
