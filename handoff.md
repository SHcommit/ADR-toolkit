# handoff.md

## Current task (2026-08-31)

ADR Toolkit `v0.2.0` minor-release implementation is complete. The
`improvements.md` P1 backlog has been fully worked down — every item that
was actionable by an agent is done, and the two that weren't (Codex
metadata compatibility, stale branch cleanup) were resolved with the
owner's decision/approval. This session's own design decisions have been
dogfooded as ADR-0007..0010.

An additional, owner-approved feature — ADR search and relationship
navigation — has also been fully implemented and merged into this branch
(see "Touched since the last handoff"). Not part of v0.2.0's original scope;
taken on after the owner asked to improve ADR navigability for real-world
OSS adoption, and promoted out of `project-roadmap.md`'s "ADR navigation and
scale" item after research into comparable OSS tools showed search +
relationship visibility are proven table-stakes regardless of this repo's
own ADR count.

The work runs in the linked worktree at `/Users/yangseunghyeon/orca/workspaces/ADR-toolkit/develop-2`
(directory name unchanged; the branch itself was renamed). Its base is the
current `origin/develop` history plus the approved design commits:

- `7b9bb8c` — initial localization/readiness design
- `b69a784` — v0.2.0 release gates, repository config, CHECK confidence, and
  report separation

Baseline verification before implementation: `212 passed` on 2026-08-30.

**Branch renamed**: `develop-2` → `feature/v0.2.0-multilingual-and-check-confidence`.
**Pushed to `origin`, PR #2 open against `develop`, CI green**:
https://github.com/SHcommit/ADR-toolkit/pull/2 — all 6 checks (5-leg pytest
matrix + `version-drift`) passing, `mergeable`. Owner approved push + PR
opening; **not** the version bump/release branch/tag — those still need
separate explicit approval.

CI caught a real pre-existing Windows-only bug on the first run (both
`windows-latest` legs failed, macOS/Ubuntu/version-drift passed):
`test_uncommitted_mode_preserves_unicode_untracked_path_and_content` in
`test_diff.py`. Root cause: none of `diff.py`'s or `git_paths.py`'s
`subprocess.run(..., text=True)` calls passed `encoding="utf-8"`, so Python
decoded git's UTF-8 output using the platform's default locale encoding —
correct on macOS/Linux, not guaranteed on Windows. Fixed in `e58d8b1` by
adding `encoding="utf-8"` explicitly to every git subprocess call in both
files; re-run confirmed all 6 checks green. This was a latent bug from
earlier CHECK-correctness work in this branch (commits `801fa4c`/`d691a33`,
predating this session's search/relationships work) — it only surfaced now
because this branch had never run CI before this PR.

## Touched since the last handoff

**Session cleanup** (see prior handoff versions in git history for full
detail): `c995904` closed Codex metadata compatibility as not applicable,
`b1a4ec5` deleted two stale remote branches, `2fa6d67` recorded ADR-0007..0010.

**ADR search and relationship navigation** — design:
`docs/superpowers/specs/2026-08-31-adr-search-and-relationships-design.md`
(`300456a`, revised after external review verification `f8b6423`).
Implementation, 14 TDD tasks, in order:

1. `20254cf` — extracted `path_under` into `core/globs.py` (pure refactor
   of `rules/conflict.py`'s prefix matching).
2. `7c95692` — `core/query.py`: `matches_keyword` (title+body fix, was
   title-only before), `matches_tags_any`, `matches_paths_exact`,
   `path_governed_by`.
3. `ff25b68` — `core/query.py`: `rank_key` deterministic ranking (5 tiers,
   no numeric score exposed publicly).
4. `7ade27d` — `core/relationships.py`: `Relationship` NamedTuple + `resolve()`.
5. `c597a30` — `core/relationships.py`: `missing_targets()` +
   `supersession_mismatches()`.
6. `c8c2b06` — migrated `related.py` onto `core/query.py`, fixed the
   body-search bug (policy unchanged: still OR-across-fields). Also found
   and fixed a real regression the migration would otherwise have
   introduced, plus one latent bug: both `matches_tags_any`/
   `matches_paths_exact` and `path_governed_by` needed a restored
   `_as_list()` guard against a malformed ADR carrying a non-list value for
   `affected_paths`/`tags` (would otherwise silently iterate a string
   character-by-character).
7. `5db2471` — `search` command core filtering (browse mode,
   AND-across-fields, OR-within-field, `--path` via `path_governed_by`).
8. `9a86666` — ranking, `--limit`/`total`/`truncated`, `query` echo.
9. `36d7048` — wired `search` into `adr.py`'s CLI.
10. `2ed781e` — `index.py` Relationships section (supersession chains +
    related lists, titles alongside IDs, entries with no relationships
    omitted).
11. `38e0d27` — localized the 5 new keys across all 8
    `scripts/i18n/*.json` catalogs.
12. `b6d9658` — `validate.py`: `BROKEN_SUPERSESSION_LINK` +
    `SUPERSESSION_MISMATCH` (errors, matching `BROKEN_RELATED_LINK`'s
    existing severity).
13. `9694f87` — documented `search` in README (with real, scratch-repo-
    verified example output) and the `related` vs `search` framing in
    SKILL.md.
14. `68e2007` — regenerated `docs/decisions/README.md` with the new
    Relationships section.

**Post-spec additions** (owner asked to add 2 of the external review's
smaller deferred items after the 14-task plan landed; graph rendering,
semantic search, and `adr serve` remain out of scope, per the review's own
§22 and this project's evidence-before-building principle):

15. `8efde92` — `core/relationships.find_cycles()` (DFS over `supersedes`
    edges only — `related` is symmetric, no cycle concept applies) +
    `validate.py`'s `SUPERSESSION_CYCLE` error.
16. `b8d93e4` — `search --id` for exact ADR lookup, combined via the same
    AND policy as every other filter (not a separate short-circuit path).

**Note for whoever writes ADR test fixtures next**: this repo's
`frontmatter.py` is a minimal custom parser, not real YAML — it only
understands `key: []` or block-style `key:\n  - item`. A flow-style
`tags: ['x']` silently parses as the literal string `"['x']"`, not a list.
Hit this exact bug while writing `test_search_command.py`'s fixtures.

Latest local verification on 2026-08-31:

- `python3 -m pytest -q` → `386 passed`, exit 0
- `python3 scripts/sync_version.py --check` → exit 0
- `adr.py validate --dir docs/decisions` → `checked: 10`, no errors (neither
  the relationship-integrity checks nor the new cycle check flag ADR-0003/
  ADR-0006's real supersession)
- `adr.py index --dir docs/decisions` regenerated cleanly, Relationships
  section correct
- `adr.py search --id ADR-0007 --dir docs/decisions --json` → real result
  verified against this repository's actual ADR-0007
- `git status --short` → clean

The detailed v0.2.0 evidence and maturity assessment (predating the search
feature) are in `docs/adr-toolkit-v0.2.0-readiness-report.md` — not
re-verified against commits since it was written; re-run its evidence
commands before treating its GO/NO-GO judgment as current. Post-release
governance is kept separate in `docs/enterprise-adoption.md`.

## Next step

`improvements.md` has exactly one open item left: the P0 release gate.
**PR #2 is open, CI green, `mergeable`**
(https://github.com/SHcommit/ADR-toolkit/pull/2). Everything left needs
separate, explicit owner approval not yet given, in order:

1. The v0.2.0 version bump (`skills/adr-toolkit/VERSION` is still `0.1.0`;
   run `scripts/sync_version.py` after bumping to propagate).
2. Merging PR #2 (into `develop`) — normal merge or squash, per repo
   convention; no merge has been authorized in this session.
3. Cutting a `release/*` branch into `master` and back into `develop`, per
   `AGENTS.md`'s Git Flow policy.
4. Pushing a `v0.2.0` tag on `master` — `.github/workflows/release.yml`
   then runs the full suite, verifies manifest versions against the tag,
   and publishes the GitHub Release automatically.

Do not perform 1-4 without asking first — each is a separate explicit
approval point, not implied by "CI is green."

`project-roadmap.md` was updated to mark "ADR navigation and scale"'s first
bullet done, with the remaining three (graph *rendering* specifically,
500+-scale sharding/real search index, semantic retrieval) still explicitly
gated on usage evidence that doesn't exist yet.

An open, undecided idea from this session: measuring how much LLM-token
input/output the deterministic core saves an agent versus doing the same
work by reading/writing everything by hand (e.g. CHECK returning a
structured finding instead of the agent scanning a full diff). Discussed but
deliberately deferred — no scope or destination (new doc section vs.
benchmarking script) has been decided.

## Open risks

- Catalog structure is deterministic, but terminology still benefits from
  native-speaker review in each supported language — now including the 5
  new Relationships-section keys.
- CHECK deliberately cannot prove prose, business rationale, or organizational
  claims; those remain human-review evidence. The exception mechanism
  extends this: an exception is recorded and annotated, never a silent pass.
- Search/relationship matching is deterministic substring/exact/prefix
  matching, untested at real scale (this repo has 10 ADRs); if this project
  grows well past that, revisit `project-roadmap.md`'s remaining
  navigation-and-scale items rather than assuming the current approach
  still holds.
- GitHub protection is intentionally unavailable in the current private plan;
  configure and API-verify it after the repository becomes public (owner's
  own follow-up, not scheduled here).
- Version bump, release branch, push, and tag are not authorized by this task.
