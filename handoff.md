# handoff.md

## Current task (2026-08-31)

`v0.2.0` release gate is in progress — the only remaining work
(`improvements.md`'s single open item). Everything else (multilingual ADR
generation, CHECK hardening, exception mechanism, ADR search and
relationship navigation) is implemented and merged into this branch; see
`changelog.md` for what shipped and `git log` for exactly how.

Work runs in the linked worktree at
`/Users/yangseunghyeon/orca/workspaces/ADR-toolkit/develop-2`, branch
`feature/v0.2.0-multilingual-and-check-confidence`, pushed to `origin`.

## Next step

**PR #2 merged into `develop`** (merge commit `3a3a482`, 2026-08-31,
regular merge not squash): https://github.com/SHcommit/ADR-toolkit/pull/2
— `origin/develop` now has all of this work. The local worktree is still
on `feature/v0.2.0-multilingual-and-check-confidence`, which can be
deleted (locally and on `origin`) once step 3 below no longer needs it —
not done automatically per `finishing-a-development-branch`'s rules.

Release gate steps, each needing separate explicit owner approval — do not
perform any of the remaining ones without asking first, "CI is green" does
not imply approval for the next step:

1. ✅ **Done** — v0.2.0 version bump (`skills/adr-toolkit/VERSION` →
   `0.2.0`, propagated via `scripts/sync_version.py`); CI re-ran green.
2. ✅ **Done** — merged PR #2 into `develop`.
3. Cut a `release/*` branch **from `develop`** into `master` and back into
   `develop`, per `AGENTS.md`'s Git Flow policy.
4. Push a `v0.2.0` tag on `master` —
   `.github/workflows/release.yml` then runs the full suite, verifies
   manifest versions against the tag, and publishes the GitHub Release.

Latest local verification (2026-08-31): `python3 -m pytest -q` → `386
passed`; `sync_version.py --check` → exit 0; `adr.py validate` → 10 ADRs,
no errors; `git status --short` → clean.

An open, undecided idea from this session: measuring how much LLM-token
input/output the deterministic core saves an agent versus doing the same
work by hand (e.g. CHECK returning a structured finding instead of the
agent scanning a full diff). Deliberately deferred — no scope or
destination decided.

## Open risks

- CHECK deliberately cannot prove prose, business rationale, or
  organizational claims; those remain human-review evidence. The exception
  mechanism extends this — an exception is recorded and annotated, never a
  silent pass.
- Search/relationship matching is deterministic substring/exact/prefix
  matching, untested at real scale (this repo has 10 ADRs); revisit
  `project-roadmap.md`'s navigation-and-scale items if that changes.
- GitHub branch/tag protection is intentionally unavailable on the current
  private plan; configure and API-verify after the repository goes public
  (owner's own follow-up, not scheduled here).
- Version bump is done; release branch, push, and tag remain unauthorized
  until the owner approves each step above.
