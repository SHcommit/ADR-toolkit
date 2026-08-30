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

## CHECK follow-ups (deferred from Plan 3's final review)

Minor/deferred findings from Plan 3's closeout review, not fixed in the
fix wave since they're either narrow edge cases or refactors better done
deliberately rather than folded into a fix commit:

- `check.py`'s `_existing_paths` walks the whole working tree via
  `rglob("*")`, skipping only `.git`. `diff.py` already shells out to
  `git ls-files`; switching to
  `git ls-files --cached --others --exclude-standard` would be faster on
  large repos and correctly honor `.gitignore` (currently a gitignored
  build artifact could satisfy a `required_path`/`file_must_exist` rule).
- `SKIP_FILES = {"README.md", "adr-template.md"}` and the
  glob/parse-filename/frontmatter-parse-with-per-file-warning loop are now
  duplicated across `related.py`, `index.py`, `validate.py`, and
  `check.py`. A shared `core/adr_dir.py::iter_adrs(adr_dir) -> (entries,
  warnings)` would collapse all four call sites.
- `references/conflict-rules.md` doesn't warn that `pattern`'s syntax
  differs by rule kind (regex for `forbidden_import`/`dependency_forbidden`,
  glob for `required_path`/`forbidden_path`) — an author copying the
  `paths` glob style into a `forbidden_import` rule's `pattern` field gets
  a regex where `**` silently never matches as expected.
- `diff.py`'s `--name-status` parsing takes only the destination path for
  a renamed file (git status char `R`), dropping the old path entirely —
  a `constraints:` rule scoped to the old location won't fire on a rename,
  and a Verification/Confirmation-referenced file that was renamed away
  isn't recognized as removed.
- `diff.py`'s second subprocess call (the `--unified=0` patch content)
  doesn't independently check its own returncode — if it fails while the
  first `--name-status` call succeeded, files get correct `change_type`
  but empty `added_lines`/`removed_lines`, silently passing every
  content-pattern rule instead of surfacing an error.
- `diff.py`'s `INVALID_REF` vs `GIT_DIFF_FAILED` error-code selection
  checks the raw `since` argument's truthiness rather than
  `mode == "since"` — near-unreachable in practice (would need
  `--staged --since <bad-ref>` together, which the CLI doesn't prevent),
  but worth tightening to `mode == "since"` if `diff.py` is touched again.

## i18n, adapters, release follow-ups (deferred from Plan 4's final review)

Minor/deferred findings from Plan 4's closeout review, not fixed in the
fix wave since they're narrow polish or genuinely need Codex's Agent
Plugins support to mature before a good fix exists:

- `adapters/codex/README.md`'s opening line slightly overclaims which
  manifest the verification exercised — it reads as endorsing
  `.codex-plugin/plugin.json`'s sibling-`skills/` auto-discovery, but the
  verified working path is Codex reading the repo-root
  `.claude-plugin/marketplace.json` instead; `.codex-plugin/`'s own
  auto-discovery was never actually exercised. Reword to scope the claim
  to what was tested.
- Relatedly, the Codex README's install step 1 (create the
  `adapters/codex/skills/adr-toolkit` symlink, per spec §17.2) is
  currently orphaned — the documented working install (steps 2-4) never
  touches it, since Codex reads the repo-root marketplace file instead.
  Kept because the spec mandates the symlink exist, but the README should
  explain why step 1 still matters once Codex's own Agent Plugins support
  (shipped 2026-08-07, very new) starts reading `.codex-plugin/` the way
  the standard describes.
- `codex plugin add` snapshots the entire repo root — including `.git/`,
  `.superpowers/`, `.pytest_cache/` — into its plugin cache. Not a defect
  in this repo's adapter, but worth knowing before ever publishing this as
  a real, standalone marketplace listing (a dedicated distribution repo
  might be warranted instead of pointing Codex at the full dev repo).
- `scripts/sync_version.py`'s `sync()` still silently skips a manifest
  that exists but has lost its declared `version` key (only a missing
  *file* is now a hard error via `require_known_paths()`) — covered by a
  test asserting the real manifests currently have the key, but the
  script itself doesn't enforce it going forward.
- `scripts/sync_version.py:104`'s `path.relative_to(REPO_ROOT)` in an
  error-reporting path would raise `ValueError` instead of the intended
  `SystemExit` if a future `MANIFEST_SPECS` entry were ever added outside
  `REPO_ROOT` — only reachable via a deliberately malformed entry today,
  not user-triggerable.
- `SKILL.md`'s line documenting the lifecycle `index --locale` invocation
  is noticeably longer than the file's otherwise-consistent ~72-column
  wrap. Cosmetic.
- Description text for the toolkit ("Initialize, record, and check
  Architecture Decision Records...") is now duplicated across four
  manifests (`.claude-plugin/plugin.json`, `SKILL.md`'s frontmatter, the
  three adapter manifests, `.claude-plugin/marketplace.json`) with slight
  wording drift between them and no sync mechanism — `sync_version.py`
  only syncs the version field, not descriptions.
- `sync_version.py`'s `json.dumps(..., indent=2)` defaults to
  `ensure_ascii=True`; harmless today since all synced values are ASCII,
  but a future non-ASCII description would get mangled into `\uXXXX`
  escapes on the next sync. Pass `ensure_ascii=False` if that becomes a
  real concern.
- `.github/workflows/test.yml`'s version-drift check step runs redundantly
  on all 5 matrix legs (3 OS × 2 Python versions minus one exclusion) —
  it's a repo-invariant check, not a platform-specific one, so one leg
  would suffice. Harmless, just slightly wasteful CI time.
- Root `README.md` is still a one-line stub at MVP-complete. Nothing
  points a new user at the four `adapters/*/README.md` install guides or
  at `create --interactive`'s no-agent-needed path. Worth writing a real
  README before any public release, alongside the license decision.
