# improvements.md

Concrete implementation backlog. Unscheduled product bets belong in
`project-roadmap.md`; current-session state belongs in `handoff.md`.

## Open

### P0 — v0.2.0 release blocking

- [ ] **Complete the remote v0.2.0 release gate.** Open the final PR, require all
  CI jobs to pass, obtain approval for the v0.2.0 version bump, merge through a
  release branch, and verify the tag points at the intended `master` commit.
  **Done when:** the readiness report's conditional GO becomes GO. Creating the
  release branch, pushing, version bumping, and tagging require owner approval.

### P1 — strongly recommended

- [ ] **Resolve Codex metadata compatibility.** Codex `quick_validate.py`
  rejects `user-invocable` and `version`, while the cross-harness contract and
  repository tests require them.
  **Done when:** a deliberate compatibility decision and verified adapter path
  replace the standing ambiguity.
- [ ] **Clean stale remote branches after reference checks.** Candidates are
  `origin/SHcommit/feat-plan-adr-toolkit` and
  `origin/feat/adr-toolkit-mvp-implement`.
  **Done when:** no open PR or release reference needs them and the owner
  explicitly approves deletion.

## Done

- [x] Added a small, deterministic schema for CHECK policy exceptions:
  `adr.py exception --input <file.json>` validates `owner`/`reason`/`scope`/
  `expiry`/`adr_id`/`rule_id` and writes `docs/decisions/exceptions/NNNN.json`
  as `EXC-NNNN`. CHECK loads active (non-expired, schema-valid) exceptions and
  annotates a matching finding's `exception` field — it never suppresses or
  downgrades the finding itself, keeping `kind`/`confidence` exactly what the
  structural evidence says. A malformed exception file degrades to a
  `BAD_EXCEPTION` warning, matching the existing ADR/constraints pattern.
- [x] Promoted CHECK's confidence classification to a stable field: every
  finding now carries `confidence` (`VERIFIED`/`VIOLATED`/`UNVERIFIABLE`)
  computed directly from its `kind`, instead of leaving that mapping for the
  agent to re-derive from prose docs each time. Updated README, SKILL.md,
  `conflict-rules.md`, and quickstart's example output to match.
- [x] Resolved `--json` semantics: adopted "always JSON to stdout" as the
  deliberate, tested contract (matching the code's own existing
  "JSON-only-stdout contract" comment and every real caller), rather than
  inventing a human-readable mode or removing the flag in a breaking change.
  `--json` is now documented via `--help` as a no-op kept for backward
  compatibility; added a regression test proving output is JSON with or
  without it; added it to the three doc examples that omitted it, for
  consistency.
- [x] Decided manifest-description ownership: `SKILL.md`'s frontmatter
  `description:` is now the single canonical source, synced by
  `sync_version.py` into `.claude-plugin/plugin.json`,
  `adapters/codex/.codex-plugin/plugin.json`,
  `adapters/gemini-cli/gemini-extension.json`, and
  `adapters/antigravity/plugin.json`, with `--check` enforcing it in CI. Fixed
  the one real drift this uncovered (`.claude-plugin/plugin.json` was missing
  "and existing decisions").
- [x] Corrected `adapters/codex/README.md`: re-verified against Codex CLI
  0.151.0 that the documented install flow works with zero
  `adapters/codex/skills/` symlink present (marketplace root resolves to the
  repo root's own `.claude-plugin/plugin.json`, whose sibling `skills/` is
  the real package), removed the misleading symlink as install step 1, and
  added an explicit section marking `.codex-plugin/plugin.json` and its
  optional symlink as structural-only, not exercised by the verified path.
- [x] Centralized ADR directory loading: `related`, `index`, `validate`, and
  `check` now share `core.adr_directory.iter_adr_files` instead of each
  redefining `SKIP_FILES` and re-walking the directory; each command keeps its
  own bad-filename/frontmatter handling (silent skip vs. reportable error).
- [x] Moved the manifest version-drift check out of the 5-leg OS/Python test
  matrix into its own single `version-drift` job, since the check is a
  repository-content invariant, not a per-platform/per-interpreter one.
- [x] Hardened `sync_version.py`: a tracked manifest that keeps its file but
  loses its `version` key now fails `--check` instead of reporting no drift;
  a manifest path outside the repo root raises the intended `SystemExit`
  instead of an unrelated `ValueError`; JSON writes use `ensure_ascii=False`
  so non-ASCII manifest content survives a sync unescaped.
- [x] Added the versioned `.adr-toolkit.json` locale contract with strict
  validation and CLI → draft → repository → English precedence.
- [x] Added deterministic INIT, CREATE, template, prompt, and INDEX rendering
  for `en/ko/ja/zh/fr/es/de/pt-BR`, with exact catalog parity and an end-to-end
  locale matrix.
- [x] Preserved Unicode ADR content while enforcing portable ASCII filenames,
  optional approved semantic slugs, and the deterministic `decision` fallback.
- [x] Kept runtime and JSON Schema locale validation in parity without breaking
  locale-less ADRs.
- [x] Made CHECK fail closed on incomplete git evidence and covered subprocess,
  rename, Unicode, tracked deletion, invalid ADR visibility, ignored-path, Git
  path-semantics, and conflicting-mode defects.
- [x] Made relative ADR directories resolve consistently against `--root` for
  INIT, CREATE, INDEX, VALIDATE, and CHECK instead of the caller's CWD.
- [x] Raised the dogfooded ADR set to the repository quality contract and
  superseded ADR-0003 with the approved ADR-0006 localization decision.
- [x] Documented repository defaults, per-command overrides, eight locales,
  semantic slugs, and CHECK confidence in README, SKILL, and quickstart.
- [x] Added a real Korean quickstart path covering repository-default locale,
  Unicode content, semantic slug, fallback filename, and localized index.
- [x] Published separate Korean v0.2.0 readiness and enterprise-adoption
  reports with measurable maturity criteria and official external references.
- [x] Passed local release evidence: 290-test full suite, version-drift check,
  six-ADR validation, stable generated index, and whitespace checks.
- [x] Integrated the MVP feature work through `develop` and released `v0.1.0`
  from `master`.
- [x] Merged PR #1 into `develop`, adding dogfooded ADRs, the root README,
  executable quickstart, and local-artifact ignore rules.
