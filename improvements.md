# improvements.md

Concrete implementation backlog. Unscheduled product bets belong in
`project-roadmap.md`; current-session state belongs in `handoff.md`.

## Open

### P0 — v0.2.0 release blocking

- [ ] **Repository locale configuration and precedence.** Add the versioned
  root `.adr-toolkit.json` contract and resolve locale as explicit CLI →
  approved input draft → repository default → `en`. Agent workflows resolve
  explicit request → request language → repository default → `en`.
  **Done when:** missing config defaults to English; malformed, unknown-version,
  unknown-key, and unsupported-locale configs fail visibly; precedence has
  focused tests.
- [ ] **Eight-locale deterministic generation.** Support
  `en/ko/ja/zh/fr/es/de/pt-BR` across INIT, interactive CREATE, input CREATE,
  templates, and INDEX without translating user prose.
  **Done when:** all catalogs exactly match the English key set and every locale
  passes INIT → CREATE → VALIDATE → INDEX in an integration matrix.
- [ ] **Portable multilingual filenames.** Preserve Unicode titles/bodies,
  accept an optional human-approved semantic ASCII slug, and fall back to
  `decision` when no ASCII slug can be derived.
  **Done when:** non-ASCII-only, mixed-script, explicit valid slug, and invalid
  slug cases have regression coverage on the ASCII filename contract.
- [ ] **ADR locale schema parity.** Add optional `locale` metadata without
  breaking existing ADRs.
  **Done when:** runtime validation and `adr.schema.json` accept the same eight
  values, reject unsupported present values, and keep locale-less ADRs valid.
- [ ] **CHECK must fail closed on incomplete git evidence.** Check both diff
  subprocess return codes, surface untracked-listing failures, preserve old and
  new rename paths, use `git ls-files --cached --others --exclude-standard` for
  existing paths, reject conflicting diff modes, and document regex versus glob
  patterns.
  **Done when:** each prior false-clean path has a failing-then-passing
  regression test and the complete CHECK suite passes.
- [ ] **Dogfooded ADR minimum quality contract.** Record the owner-approved
  decision maker, add `locale: en`, represent retrospective reconstruction
  truthfully, strengthen affected paths/confirmations, and supersede ADR-0003
  with the approved v0.2.0 localization/config decision.
  **Done when:** repository ADR quality tests, `validate`, lifecycle links, and
  a regenerated zero-diff index all pass.
- [ ] **Released behavior is documented.** Explain repository defaults,
  per-command overrides, eight locales, semantic slug confirmation, and CHECK's
  limited verification confidence in README/SKILL/quickstart.
  **Done when:** documentation-contract tests pass and every shown CLI command
  has been executed successfully in a scratch repository.
- [ ] **Fresh release verification.** Run the full suite, version-drift check,
  repository ADR validation/index stability, and diff whitespace checks.
  **Done when:** the readiness report contains command evidence for every P0
  gate and recommends GO; version bump/tag still require separate approval.

### P1 — strongly recommended

- [ ] **Publish the Korean readiness and enterprise-adoption reports.** Keep
  release evidence separate from post-release team/enterprise governance.
  **Done when:** facts, external practices, inferences, recommendations, costs,
  and measurable signals are visibly separated and cited.
- [ ] **Add a non-Latin quickstart.** Demonstrate repository-default locale,
  Unicode title, approved semantic slug, and localized index with real output.
  **Done when:** the example commands execute byte-for-byte as documented.
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

- [x] Integrated the MVP feature work through `develop` and released `v0.1.0`
  from `master`.
- [x] Merged PR #1 into `develop`, adding dogfooded ADRs, the root README,
  executable quickstart, and local-artifact ignore rules.
