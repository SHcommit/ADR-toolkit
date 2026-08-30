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

- [ ] **Centralize ADR directory loading.** Replace duplicated
  `SKIP_FILES`/filename/frontmatter loops in related/index/validate/check with a
  focused shared iterator.
  **Done when:** all four commands retain their warning semantics and tests pass.
- [ ] **Correct Codex adapter claims.** Scope the README to the root
  `.claude-plugin/marketplace.json` flow actually exercised and explain why the
  adapter-local symlink remains relevant to native `.codex-plugin` discovery.
  **Done when:** every claim maps to a verified command or is explicitly marked
  structural-only.
- [ ] **Harden version synchronization.** Fail when a tracked manifest loses
  its version key, preserve intended `SystemExit` outside the repo root, and use
  `ensure_ascii=False` for JSON writes.
  **Done when:** focused regression tests cover all three paths.
- [ ] **Decide manifest-description ownership.** Description text has drifted
  across manifests while only versions are synchronized.
  **Done when:** one canonical source and a check are implemented, or an ADR
  explicitly accepts independent descriptions.
- [ ] **Avoid redundant version-drift CI work.** Run the repository-invariant
  sync check once instead of on every OS/Python matrix leg.
  **Done when:** test coverage remains cross-platform and one required job owns
  the drift check.
- [ ] **Resolve `--json` semantics.** Every subcommand parses `--json` but always
  emits JSON.
  **Done when:** either a human-readable mode exists with compatibility tests or
  a future breaking-release decision removes the inert flag.
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
