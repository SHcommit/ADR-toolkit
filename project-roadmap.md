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
