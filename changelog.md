# changelog.md

Lightweight human-readable summary of meaningful repository changes.

## Unreleased

- `--dir`/`--root` now reject a relative path that resolves outside the
  given root, closing a path-escape gap.
- CI now measures branch coverage (currently 93%) and fails below 85%.
- Added a `mypy --strict` CI gate over the fully-typed core modules
  (`atomic_io`, `telemetry`, the new `contracts` module of TypedDict result
  shapes).
- Added `adr.py --diagnostic` (must precede the operation name) to include
  an `elapsed_ms` timing field in the JSON result.
- Verified at the OS level (fork + SIGKILL) that a process killed mid-write
  never leaves a torn ADR file.
- Extracted a shared adapter-manifest validator (`scripts/adapter_sdk.py`)
  used by all 4 manifest-based harness adapters' tests.
- ADR and exception creation, and SUPERSEDE's two-file update, are now
  atomic and race-free under concurrent invocation (file locking + write to
  a temp file followed by an atomic rename).
- CHECK's author-supplied `constraints:` regex patterns now have a 0.25s
  evaluation timeout on Linux/macOS, closing a ReDoS risk (Windows CI is
  unaffected but not yet guarded — tracked in `improvements.md`).
- INDEX's generated decision-log README now escapes ADR titles, closing a
  Markdown link-injection risk.
- Uncaught errors now log a structured, correlation-ID-tagged JSON line to
  stderr (`ADR_TOOLKIT_LOG_LEVEL` controls the threshold) instead of
  disappearing silently; the same correlation ID appears in the stdout
  JSON error response.
- Added a `harness-parity` CI job that installs the real Codex CLI and
  Gemini CLI and drives their own plugin/extension commands (marketplace
  add, install, list) against this repo, then runs `preflight`/`init`/
  `validate` from the installed snapshot on every push and pull request —
  catching a broken adapter before a user hits it, not after.
- Verified the Antigravity CLI adapter end to end against the `agy` CLI
  (validate/install/list plus the script layer); `adapters/antigravity/README.md`
  corrected from "unverified" to a recorded transcript, matching the
  Codex/Gemini adapters' documented depth.
- Added `CODE_OF_CONDUCT.md` and GitHub issue templates (bug report,
  feature request) as public-repository readiness ahead of the eventual
  switch to public.
- Recorded ADR-0011 for the relationship graph and public-readiness
  decisions.
- Added ADR relationship graph navigation: `adr.py index` now embeds a Mermaid
  graph in the generated decision log when relationships exist, and
  `adr.py graph` exports standalone `relationships.mmd` plus a crisp SVG
  navigation artifact without requiring Node, Mermaid CLI, or browser
  rendering.
- Added public repository readiness docs: `CONTRIBUTING.md`, `SECURITY.md`,
  and a pull request template covering ADR impact and local verification.
- Added `adr.py search`: finds an existing ADR by keyword (title **and**
  body — `related`'s keyword match was title-only before), tags, status,
  `--id`, or the real file path it governs, with deterministic best-match
  ordering and `--limit`/`total`/`truncated` for bounding results. Added a
  Relationships section (supersession chains + related lists, titles
  alongside IDs) to the generated `docs/decisions/README.md`, localized
  across all 8 catalogs, and `validate` checks for broken supersession
  links, one-sided supersession edits, and supersession cycles.
- Added CHECK policy exceptions: `adr.py exception` validates and records a
  schema-checked, owned, scoped, time-boxed exception; CHECK annotates a
  matching finding with it but never suppresses or downgrades the finding —
  an exception is visible evidence, not a silent pass.
- Promoted CHECK's violation classification to a stable `confidence` field
  (`VERIFIED`/`VIOLATED`/`UNVERIFIABLE`) on every finding, instead of an
  agent re-deriving it from documentation each run.
- Fixed a Windows-only bug where CHECK's git evidence gathering
  (`diff.py`/`git_paths.py`) decoded subprocess output using the platform's
  default locale encoding instead of UTF-8, garbling Unicode paths/content
  on Windows CI while working correctly on macOS/Linux.
- Hardened `scripts/sync_version.py` against three silent-drift bugs
  (a tracked manifest losing its version key, a manifest path outside the
  repo root crashing instead of failing cleanly, non-ASCII manifest content
  being escaped on write) and extended it to keep manifest `description`
  fields in sync with `SKILL.md`'s frontmatter, the same way `version`
  already was.
- Formalized `--json` as a documented no-op: every command has always
  printed JSON regardless of the flag; `--help` now says so explicitly
  instead of implying a choice that doesn't exist.
- Corrected repository ADR provenance and lifecycle: existing ADRs now name
  an approved decision maker and locale, and ADR-0006 (repository-default
  locale generation) supersedes ADR-0003 (index-only localization)
  bidirectionally. This session's own design decisions were recorded as
  ADR-0007..0010 (CHECK confidence field, exception mechanism, `--json`
  contract, and a closed-as-not-applicable Codex tooling question).
- Bumped to v0.2.0.
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
