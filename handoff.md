# handoff.md

## Current task (2026-08-31)

ADR Toolkit `v0.2.0` minor-release implementation is complete. The
`improvements.md` P1 backlog has been fully worked down — every item that
was actionable by an agent is done, and the two that weren't (Codex
metadata compatibility, stale branch cleanup) were resolved with the
owner's decision/approval. This session's own design decisions have been
dogfooded as ADR-0007..0010.

Now implementing an additional, owner-approved feature: ADR search and
relationship navigation (see "Next step" below) — not part of v0.2.0's
original scope, taken on after the owner asked to improve ADR
navigability for real-world OSS adoption.

The work runs in the linked worktree at `/Users/yangseunghyeon/orca/workspaces/ADR-toolkit/develop-2`
(directory name unchanged; the branch itself was renamed). Its base is the
current `origin/develop` history plus the approved design commits:

- `7b9bb8c` — initial localization/readiness design
- `b69a784` — v0.2.0 release gates, repository config, CHECK confidence, and
  report separation

Baseline verification before implementation: `212 passed` on 2026-08-30.

**Branch renamed**: `develop-2` → `feature/v0.2.0-multilingual-and-check-confidence`
(local rename only; not yet pushed, no upstream configured).

## Touched since the last handoff

- `c995904` — closed the Codex metadata compatibility item as not
  applicable: `quick_validate.py` belongs to Codex's local skill-creator
  tool, never the actual plugin install path (independently re-verified).
- `b1a4ec5` — deleted the two stale remote branches
  (`origin/SHcommit/feat-plan-adr-toolkit`,
  `origin/feat/adr-toolkit-mvp-implement`); both were fully merged into
  `origin/develop` with no open PR referencing either.
- `2fa6d67` — recorded ADR-0007..0010 for this session's own design
  decisions, scored via `adr.py significance` before writing:
  - ADR-0007 (10, recommended) — CHECK's `kind`→`confidence` mapping
    promoted to a stable output field.
  - ADR-0008 (12, recommended) — deterministic CHECK policy exceptions,
    schema-validated and annotate-only, never suppressing a violation.
  - ADR-0009 (7, recommended) — `--json` is a documented no-op; CLI output
    is always JSON.
  - ADR-0010 (4, optional) — Codex `quick_validate.py` incompatibility is
    not this project's problem, with the verification evidence recorded.

(Earlier in this session — still current, not re-listed in detail: `b9e0ec3`
sync_version.py hardening, `baa0987` CI dedup, `2f2a8de` ADR directory
centralization, `061d44e` Codex adapter doc fix, `5d37bef` manifest
description ownership, `63c4c85` `--json` implementation, `2c73af6` CHECK
confidence field implementation, `6e68b5d` exception schema implementation
— ADR-0007..0010 above are the *rationale records* for the last three of
these.)

Latest local verification on 2026-08-30:

- `python3 -m pytest -q` → `327 passed`, exit 0
- `python3 scripts/sync_version.py --check` → exit 0
- `adr.py validate --dir docs/decisions` → `checked: 10`, no errors
- `adr.py index --dir docs/decisions` regenerated cleanly
- `git status --short` → clean

The detailed v0.2.0 evidence and maturity assessment are in
`docs/adr-toolkit-v0.2.0-readiness-report.md` (not re-verified against the
commits since it was written — re-run its evidence commands before treating
its GO/NO-GO judgment as current); post-release governance is kept separate
in `docs/enterprise-adoption.md`, whose §8 "다음 구현 후보" now reflects
items 1, 3, and 4 as done.

## Next step

**In progress, executing inline (not subagent-driven) per owner's request for
tight commit/handoff cadence in case the session runs out and Codex picks up
next.** Implementing the ADR search + relationship navigation feature:

- Design: `docs/superpowers/specs/2026-08-31-adr-search-and-relationships-design.md`
  (`300456a`, revised after external review verification `f8b6423`, owner-approved).
- Plan: `docs/superpowers/plans/2026-08-31-adr-search-and-relationships.md`
  — **gitignored, not committed to git; it only exists in this worktree's
  filesystem.** If a fresh session (this one or Codex) needs to resume and that
  file is somehow gone, re-derive the remaining tasks from the spec above (which
  *is* committed) plus the "Tasks completed so far" list below — the spec's own
  "Implementation sequencing" section has the same 9-step order the plan's 14
  tasks were broken out from.
- The plan has 14 bite-sized TDD tasks. **Follow strict TDD**: write the failing
  test, watch it fail, write minimal code, watch it pass, commit — one task at a
  time, in order, exactly as the plan file specifies (real code and test bodies
  are already written out in the plan; don't improvise different ones).

**Tasks completed so far (commits, in order):**
1. `20254cf` — extracted `path_under` into `core/globs.py`, refactored
   `rules/conflict.py` to use it (pure refactor, `test_conflict.py`/
   `test_check.py` still pass unmodified).
2. `7c95692` — `core/query.py`: `matches_keyword` (title+body fix),
   `matches_tags_any`, `matches_paths_exact`, `path_governed_by`.
3. `ff25b68` — `core/query.py`: `rank_key` deterministic ranking (5 tiers,
   no numeric score exposed publicly).
4. `7ade27d` — `core/relationships.py`: `Relationship` NamedTuple + `resolve()`.
5. `c597a30` — `core/relationships.py`: `missing_targets()` +
   `supersession_mismatches()`.
6. `c8c2b06` — migrated `related.py` onto `core/query.py`, fixed body-search
   bug; **also found and fixed a real regression while doing this**: the
   migration would have dropped `related.py`'s original `_as_list()` guard
   against a malformed ADR carrying a non-list value for `affected_paths`/
   `tags` (e.g. a plain YAML string instead of a list), which would silently
   decompose into individual characters and produce nonsense matches. Fixed
   by restoring the guard as `_as_list()` inside `core/query.py` itself,
   applied to all three matchers including `path_governed_by` (which had the
   same latent bug with no prior test catching it — added one).
7. `5db2471` — `search` command core filtering (browse mode,
   AND-across-fields, OR-within-field, `--path` via `path_governed_by`).
   **Note for whoever writes ADR test fixtures next**: this repo's
   `frontmatter.py` is a minimal custom parser, not real YAML — it only
   understands `key: []` or block-style `key:\n  - item`. A flow-style
   `tags: ['x']` silently parses as the literal string `"['x']"`, not a
   list. Hit this exact bug writing `test_search_command.py`'s fixture
   helper; fixed by rendering block-list YAML instead.
8. `9a86666` — ranking, `--limit`/`total`/`truncated`, `query` echo.
9. `36d7048` — wired `search` into `adr.py`'s CLI (added `STATUSES` import
   from `scripts.core.lifecycle` for `--status` choices).

10. `2ed781e` — `index.py` Relationships section (supersession chains +
    related lists, titles shown alongside IDs, entries with no
    relationships omitted).
11. `38e0d27` — localized the 5 new keys across all 8
    `scripts/i18n/*.json` catalogs + `test_locale.py`'s `REQUIRED_KEYS`.
12. `b6d9658` — `validate.py`: `BROKEN_SUPERSESSION_LINK` +
    `SUPERSESSION_MISMATCH` (errors, matching `BROKEN_RELATED_LINK`'s
    existing severity — `validate.py` has no warnings mechanism). Verified
    against this repo's real 10 ADRs: `ok: true`, no errors.

Full suite at this point: `379 passed`.

**Tasks remaining (plan file has full code for each):**
13. Docs: README (search usage + AND/OR semantics statement) + SKILL.md
    (`related` vs `search` framing) — run every shown command in a scratch
    repo first, don't hand-write example output.
14. Final verification: full suite, `sync_version.py --check`,
    `validate`/`index` against this repo's real 10 ADRs, `git diff --check`,
    commit the regenerated `docs/decisions/README.md`, then update
    `improvements.md`/`handoff.md` to mark this feature done.

After Task 14: `improvements.md` will have exactly one open item left, the P0
release gate (unchanged from before this feature started).

Once that work lands: `improvements.md` still has exactly one open item, the
P0 release gate. Open the final PR (from
`feature/v0.2.0-multilingual-and-check-confidence` against `develop`), get
required CI green, get the owner's approval for the v0.2.0 version bump
(`skills/adr-toolkit/VERSION` is still `0.1.0`), merge through a release
branch, and verify the tag lands on the intended `master` commit. The branch
has not been pushed to `origin` yet (no upstream configured) — the owner has
said they'll handle the public-repository transition themselves later, and
push/PR have not been authorized in this session.

`project-roadmap.md`'s remaining items (everything except "ADR navigation and
scale," now superseded by the spec above) were reviewed end to end: each is
explicitly gated on usage evidence or a separate design decision that doesn't
exist yet — nothing else there is actionable now.

An open, undecided idea from this session: measuring how much LLM-token
input/output the deterministic core saves an agent versus doing the same
work by reading/writing everything by hand (e.g. CHECK returning a
structured finding instead of the agent scanning a full diff). Discussed but
deliberately deferred — no scope or destination (new doc section vs.
benchmarking script) has been decided.

## Open risks

- Catalog structure is deterministic, but terminology still benefits from
  native-speaker review in each supported language.
- CHECK deliberately cannot prove prose, business rationale, or organizational
  claims; those remain human-review evidence. The exception mechanism
  extends this: an exception is recorded and annotated, never a silent pass.
- GitHub protection is intentionally unavailable in the current private plan;
  configure and API-verify it after the repository becomes public (owner's
  own follow-up, not scheduled here).
- Version bump, release branch, push, and tag are not authorized by this task.
