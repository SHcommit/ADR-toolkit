# handoff.md

## Current task

Completed Production Readiness P1/P2 Backlog Improvements via Parallel
Subagent Execution (Groups A-F); all 550 tests passing. Also added a Cline CLI
adapter (`adapters/cline/`) so Cline CLI and ClinePass users can install the
`skills/adr-toolkit` package — a README-only adapter, verified against Cline CLI
3.0.61 (GitHub issue #19).

## Scope

- Updated `Agent-toolkit` plugin bundle to v0.3.6.
- Production Readiness Audit completed for `ADR-toolkit` (`analyzing-system`).
- Implemented and verified all High (P1) and Medium (P2) action items:
  - Group A: `.adr-toolkit.json` `adr_dir` config & `ADR_DIR`/`ADR_LOCALE` env vars.
  - Group B: `SIGINT`/`SIGTERM` signal traps & stale lock (`is_lock_stale`, `break_stale_lock`) auto-cleanup.
  - Group C: `adoption_metrics.py` (41KB) refactored into `scripts/adoption_metrics/` subpackage.
  - Group D: `skills/adr-toolkit/scripts/commands/doctor.py` (`adr doctor` diagnostic command).
  - Group E: 10MB file size cap & streaming parse protection in `frontmatter.py`.
  - Group F: `--verbose`, `--debug`, `--quiet` logging flags & `doctor` subcommand integrated in `adr.py`.

## Next step (for a new session picking this up cold)

All P1/P2 Production Readiness backlog items are resolved and committed, and
the Cline CLI adapter (`adapters/cline/`, GitHub issue #19) is merged. Remaining
future work is Low priority (CODEOWNERS once there are 2+ qualified
maintainers, organization-wide governance once there are 2+ repositories).
Concretely:

1. `improvements.md`'s `### Low` → audit-report sub-group has exactly 1
   item left (Antigravity in `harness-parity`), blocked on `agy` having
   no public package registry — don't start it without re-verifying that
   fact changed. Its enterprise-adoption.md sub-group has 3
   precondition-gated items (repository going public, 2+ maintainers,
   2+ repositories) — **not pure code tasks**.
2. A GitHub Wiki was considered and explicitly declined for now — this
   project's docs-as-ADRs model (versioned, reviewed, tied to releases)
   already covers the need; a wiki would fragment that. Revisit only
   once the repo is public and community-contributed FAQ/tutorial
   content that doesn't fit README/examples actually starts
   accumulating.
3. If the user says "continue" without naming a task: say there is no
   ready-to-start backlog item and ask what's next rather than
   inventing scope.
4. If the user references a new audit finding or a fresh problem: use
   the pattern this project uses for hardening work — writing-plans ->
   executing-plans, TDD, one commit per task, verify real test/mypy
   output before each commit — rather than skipping straight to edits.
5. This repository enforces a local `.githooks/pre-push` hook that
   blocks direct pushes to `develop`/`master` (no GitHub branch
   protection is configured — the repo is private, which is a GitHub
   Pro-only feature — so the hook is the *only* enforcement). Any merge
   into either branch needs a short-lived branch + `gh pr create` +
   `gh pr merge`, not a direct push. A release follows Git Flow: tag
   from `master` only, after a `release/*` (or `hotfix/*` for a
   post-release bug) branch merges in via PR, then merge `master` back
   into `develop`.
6. GitHub Artifact Attestation (`.github/workflows/release.yml`) is
   skipped while this repository is private (GitHub rejects it for a
   user-owned private repo) and starts running automatically once the
   repo goes public — no workflow change needed then.

## Verification

`python3 -m pytest tests/unit tests/integration -q` (550 tests passing) and
`python3 scripts/sync_version.py --check` passed cleanly.

## Open risks

- The ReDoS runtime timeout (`rules/conflict.py`) is POSIX-only.
- `supersede.py` guarantees single-file atomicity, but true two-phase multi-file commit across pair updates is scoped out.
