# handoff.md

## Current task (2026-08-31)

**v0.2.0 is released.** The full Git Flow release gate that
`improvements.md` had listed as P0 is done:

1. PR #3 (`feature/project-roadmap-implements` -> `develop`) merged at
   `36af56c`.
2. `release/v0.2.0` cut from `develop`, PR #4 (`release/v0.2.0` -> `master`)
   merged at `4b5dded`.
3. `v0.2.0` tag pushed on `master`; `.github/workflows/release.yml` ran
   clean (tests, sync-check, tag/VERSION match) and published
   https://github.com/SHcommit/ADR-toolkit/releases/tag/v0.2.0.
4. `feature/project-roadmap-implements` and `release/v0.2.0` deleted
   locally and on origin (both fully merged first, verified with
   `git merge-base --is-ancestor`).

This doc-only cleanup (`changelog.md`, `improvements.md`, this file) is on
branch `docs/post-release-wrapup`, based on current `origin/develop`
(`36af56c`) -- not yet pushed or PR'd.

Session summary (everything shipped in v0.2.0 beyond what was already on
`develop` before this session):

- ADR relationship graph: `adr.py graph --format mermaid|svg|both`,
  Mermaid embed in `adr.py index`. Recorded as ADR-0011.
- Public repository hygiene: `CONTRIBUTING.md`, `SECURITY.md`,
  `.github/PULL_REQUEST_TEMPLATE.md`, `CODE_OF_CONDUCT.md`,
  `.github/ISSUE_TEMPLATE/{bug_report,feature_request}.md`.
- Harness parity re-verified end-to-end against the real CLIs (Codex
  0.151.0, Gemini 0.46.0, Antigravity's `agy` 1.1.13 -- previously
  undocumented as available). New `harness-parity` CI job automates the
  Codex/Gemini checks; confirmed green on GitHub's real `ubuntu-latest`
  runner (not just locally) before it was trusted. Antigravity stays
  manual-only (`agy` has no package-registry distribution).
- `project-roadmap.md` audited against the codebase and narrowed to what's
  actually still open, including a recorded decision *not* to build a
  SessionStart-style hook right now even though Codex/Gemini both gained
  hook extension points this session -- no usage evidence supports it, and
  it cuts against the project's own minimal-interruption principle.

## Next step

1. Push `docs/post-release-wrapup`, open a PR into `develop`, merge once
   CI is green (small doc-only diff: `changelog.md` unreleased-section
   entries for this session's work, `improvements.md`'s Open section
   cleared).
2. This worktree currently sits on `docs/post-release-wrapup`; `develop`
   itself is checked out in another worktree
   (`/Users/yangseunghyeon/Development/ADR-toolkit`), so `git checkout
   develop` here will fail -- branch from `origin/develop` instead, the
   way this branch was created.
3. `project-roadmap.md` has no unblocked items left: every remaining
   section (Conflict detection depth, ADR navigation and scale,
   Internationalization, Public and enterprise governance, Ecosystem
   integration, Lifecycle research) is gated on usage evidence that
   doesn't exist yet, or -- for Public and enterprise governance
   specifically -- on the repository actually going public, which the
   owner has deferred deliberately ("조만간 할거야", not now). Don't start
   any of them without a fresh signal (real user report, real scale, real
   non-English contributor) or explicit owner direction.

Do not perform merge, release branch, push, or tag operations without
explicit owner approval -- that approval was given and executed this
session for v0.2.0 specifically; it does not carry forward to future
releases.

## Latest local verification

At `v0.2.0` tag / `master` HEAD (`4b5dded`):

- `python3 -m pytest -q` -> `395 passed`
- `python3 scripts/sync_version.py --check` -> exit 0
- GitHub Actions `release` workflow (run 33367157711): tests, sync-check,
  tag/VERSION match, and `Create GitHub Release` all green, ~22s total.
- Both `harness-parity` CI runs on PR #3 and PR #4 passed on GitHub's real
  `ubuntu-latest` runner, matching local dry-run output exactly.

## Open risks

- `adr.py check --uncommitted` reports a `VIOLATED` finding for superseded
  ADR-0003 when changes touch `index.py`; this is expected (ADR-0006
  supersedes ADR-0003) and was already noted in PR review, not a code
  defect.
- CHECK deliberately cannot prove prose, business rationale, or
  organizational claims; those remain human-review evidence.
- Search/relationship matching is deterministic substring/exact/prefix
  matching, untested at real scale (11 ADRs today). Revisit roadmap scale
  items only if an adopting repository actually reaches hundreds of ADRs.
- GitHub branch/tag protection is intentionally unavailable on the current
  private plan; configure and API-verify after the repository goes public
  (owner has deferred this deliberately, not blocked on it).
