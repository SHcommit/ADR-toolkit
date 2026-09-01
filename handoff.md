# handoff.md

## Current task (2026-09-01)

**The Critical hardening pass is done.** All 4 Critical-risk findings from
`docs/adr-toolkit-audit-report.md` are implemented, tested, and committed
on `feature/analyzing-adr-toolkit`, following
`docs/superpowers/plans/2026-09-01-critical-hardening.md` (gitignored by
convention, still on disk in this worktree) task-by-task with TDD:

1. `fc46830` feat: add atomic write and directory lock primitives
2. `49ede49` fix: make ADR creation race-free under concurrent invocation
3. `68bbd98` fix: make exception creation race-free under concurrent invocation
4. `cec7215` fix: make SUPERSEDE writes atomic and lock-protected
5. `c0ff907` fix: add ReDoS timeout guard to CHECK's author-supplied regex patterns
6. `7afdcd5` fix: escape ADR titles in generated README to prevent link injection
7. `11c8f4b` feat: add structured stderr logging with correlation IDs

`improvements.md`'s Critical section is now empty (items removed per this
file's own convention: resolved work lives in `changelog.md`'s Unreleased
section + git history, not duplicated into `## Done`). Full suite: 415
passed (up from 395 at session start).

Two real regressions were caught by TDD mid-session and fixed before
committing, worth knowing if touching this code again:
- `create.py`/`exception.py`: naively wrapping everything in
  `adr_directory_lock` made *dry runs* (and, for `exception.py`,
  *schema-validation failures*) create the directory + lock file as a side
  effect, breaking existing tests that assert nothing is created. Fixed by
  keeping preview/validation paths outside the lock and only locking the
  actual allocate-and-write step.
- `supersede.py`: two existing tests monkeypatched `Path.write_text`
  directly to simulate a write failure; that seam disappeared once writes
  route through `atomic_io.atomic_write_text`, so both were retargeted to
  patch `supersede.atomic_io.atomic_write_text` instead (same intent, same
  assertions).

## Scope for this worktree

Excluded here, being handled elsewhere -- do not touch:

- Domains 1 (core/plugin architecture) and 5 (governance/FSM) from the
  audit report -- already scored 72/80, mostly "no action needed" per the
  audit itself.
- Anything Antigravity (`agy`) adapter-related -- owner is working on this
  in another branch.
- Automatic version sync -- owner is working on this in another worktree;
  as a direct consequence, **do not touch `.github/workflows/release.yml`
  for any reason**. Two backlog items (High: supply-chain checksums/
  signing; a note under 8.4 about auto-version-bump direction) were
  deliberately deferred to that other worktree for exactly this reason --
  see the "(다른 워크트리 확인)" flags in `improvements.md`.
- README prose (root README.md, `adapters/*/README.md` content) -- another
  worktree. The Task 6 fix above touched `commands/index.py` -- that's a
  security fix in the *generator code* for `docs/decisions/README.md`, not
  README prose, and correctly stayed in scope here.

## Next step

Nothing is currently in flight. `improvements.md`'s remaining backlog
(High: repository path escape guard, test coverage measurement, mypy/
TypedDict, diagnostic/timing mode, chaos SIGKILL test, adapter SDK
extraction, plus the two other-worktree-flagged items; Medium: JSON Schema
single-source-of-truth, common error base class, output contract schema
freeze, parsing cache, bulk-ADR benchmark, TTY-aware CLI output) is
unscheduled -- **ask the owner before starting any of it**. The
Critical-only scope for the pass just completed, and the domain/worktree
exclusions above, were the owner's explicit calls in conversation, not
something derivable from the audit report alone.

## Verification

Full suite: `python3 -m pytest tests/unit tests/integration -v` -> 415
passed as of commit `11c8f4b`.

## Open risks

- The ReDoS guard is POSIX-only (`signal.SIGALRM`); Windows CI is
  unaffected but unguarded against catastrophic-backtracking patterns --
  a known, documented gap, not a regression introduced by this work.
- `supersede.py`'s two-file update guarantees each individual file is
  never torn by a mid-write crash, but does not guarantee the *pair*
  stays consistent if the process is killed between the two atomic writes
  -- true two-phase commit across files was explicitly scoped out (see
  the plan's Task 4 code comments). The backlog's "카오스(SIGKILL)
  복원력 테스트" High item follows up on this.
- Every successful `create`/`exception`/`supersede` call now leaves a
  `.adr-toolkit.lock` (0-byte, dotfile) inside `docs/decisions/` and
  `docs/decisions/exceptions/` permanently -- this is intentional (it's
  the cross-process mutex), doesn't match `*.md`/`*.json` globs so nothing
  else picks it up, but is a new, permanent artifact worth knowing about
  if someone notices it in a repo diff.
- (carried over from the audit, still true) CHECK deliberately cannot
  prove prose, business rationale, or organizational claims; those remain
  human-review evidence.
- (carried over, still true) GitHub branch/tag protection is unavailable
  on the current private plan; revisit once the repository goes public --
  owner's stated plan is to do that after most audit findings are done and
  the version bumps to 1.0.0 (see project memory
  `project_v1_public_release_plan`).
