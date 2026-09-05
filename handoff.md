# handoff.md

## Current task

Expanded `improvements.md` with High and Medium backlog items covering ReDoS cross-platform safety, 2-phase atomic transaction rollback, ADR overlap/similarity Eval infrastructure, weekly maintenance automation, PR significance bot, frontmatter auto-linter, interactive graph visualization, and code drift detection.

## Scope

- Domains 1 (core/plugin architecture) and 5 (governance/FSM) from the
  audit report are out of scope — already scored well.
- README prose (root `README.md`, `adapters/*/README.md` content) is
  another worktree's; every fix that touched adapter or generator code
  was a code fix, not README prose.
- `scripts/adoption_metrics.py` is complete; future changes should
  preserve its provider-neutral evidence contracts and JSON-only stdout
  behavior.

## Next step (for a new session picking this up cold)

Review the newly expanded `improvements.md` High/Medium items and pick an implementation candidate (e.g. `adr lint --fix` or ReDoS cross-platform guard).


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

`python3 -m pytest tests/unit tests/integration -q` and
`python3 scripts/sync_version.py --check` should both pass before any
commit; `mypy --strict` covers the fully-typed core modules
(`atomic_io`, `telemetry`, `contracts`) via CI's `type-check` job. CI
also runs `examples-drift`, `pr-title-check`, `version-drift`, and
`harness-parity` (installs the real Codex/Gemini CLIs) alongside the
coverage-gated (85%) `pytest` job.

## Open risks

- The ReDoS runtime timeout (`rules/conflict.py`) is POSIX-only; a
  static nested-quantifier check in `core/constraints.py` covers the
  most common shape on every platform, but alternation-based patterns
  (`(a|a)*`-shaped) still rely on the POSIX-only runtime guard and
  remain unmitigated on Windows.
- `supersede.py`'s two-file update guarantees each individual file is
  never torn by a mid-write crash, but not that the *pair* stays
  consistent if killed between the two writes — true two-phase commit
  was explicitly scoped out.
- Every successful `create`/`exception`/`supersede` call leaves a
  `.adr-toolkit.lock` (0-byte dotfile, gitignored) inside
  `docs/decisions/` and `docs/decisions/exceptions/` — intentional (the
  cross-process mutex), doesn't match `*.md`/`*.json` globs.
- `core/contracts.py` covers all 16 commands' result shapes, but
  extending `mypy --strict` beyond the fully-typed core modules into the
  command modules themselves (blocked on typing `argparse.Namespace`
  args) is still future work.
- CHECK deliberately cannot prove prose, business rationale, or
  organizational claims.
- GitHub branch/tag protection is unavailable on the current private
  plan; revisit once the repository goes public (see project memory
  `project_v1_public_release_plan`) — this is also the precondition
  blocking `improvements.md`'s public-transition ruleset item.
