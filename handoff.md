# handoff.md

## Current task (2026-09-01)

Executing `docs/superpowers/plans/2026-09-01-critical-hardening.md` --
implementation plan for the 4 Critical-risk findings from
`docs/adr-toolkit-audit-report.md` (also tracked in `improvements.md`'s
`## Open` -> `### Critical` section):

1. Atomic file writes + ID allocation lock (`core/atomic_io.py`, wired into
   `create.py`, `exception.py`, `supersede.py`).
2. ReDoS timeout guard for author-supplied regex (`rules/conflict.py`).
3. Markdown link-injection escape for ADR titles in the generated
   `docs/decisions/README.md` (`core/rendering.py`, `commands/index.py`).
4. Structured stderr logging with correlation IDs (`core/telemetry.py`,
   wired into `adr.py`'s global exception handler).

The plan is split into 8 tasks (Task 1-7 = one deliverable each, Task 8 =
close out the backlog docs). Each task ends with its own commit, so
**`git log --oneline` against the plan's task list is the source of truth
for what's already done** if this session is interrupted -- check which of
these commit messages exist before resuming (and cross-check the plan
file's own `- [ ]`/`- [x]` checkboxes, which are updated as steps land):

- `feat: add atomic write and directory lock primitives` (Task 1)
- `fix: make ADR creation race-free under concurrent invocation` (Task 2)
- `fix: make exception creation race-free under concurrent invocation` (Task 3)
- `fix: make SUPERSEDE writes atomic and lock-protected` (Task 4)
- `fix: add ReDoS timeout guard to CHECK's author-supplied regex patterns` (Task 5)
- `fix: escape ADR titles in generated README to prevent link injection` (Task 6)
- `feat: add structured stderr logging with correlation IDs` (Task 7)
- `docs: close out Critical hardening backlog items` (Task 8)

This session chose **inline execution** (`superpowers:executing-plans`),
not subagent-driven -- a fresh session resuming should do the same unless
the owner says otherwise.

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
  worktree. Task 6's fix to `commands/index.py` is a security fix in the
  *generator code* for `docs/decisions/README.md`, not README prose, and
  correctly stays in scope here -- don't confuse the two if asked to skip
  "README work".

## Next step

If resuming: open `docs/superpowers/plans/2026-09-01-critical-hardening.md`,
find the first unchecked step, confirm against `git log` that its task's
commit doesn't already exist, and continue from there with
`superpowers:executing-plans`.

After Task 8 lands, the remaining backlog (`improvements.md`'s High/Medium
sections) is unscheduled -- ask the owner before starting any of it. The
Critical-only scope for this pass, and the domain/worktree exclusions
above, were the owner's explicit calls in conversation, not something
derivable from the audit report alone.

## Verification

Full suite: `python3 -m pytest tests/unit tests/integration -v`.
Baseline before this session's changes: 395 passed. Expect it to grow by
roughly 15-18 tests across Tasks 1-7 (see the plan file's per-task test
files for the exact count).

## Open risks

- The ReDoS guard (Task 5) is POSIX-only (`signal.SIGALRM`); Windows CI is
  unaffected but unguarded against catastrophic-backtracking patterns --
  a known, documented gap in the audit report, not a regression introduced
  by this work.
- `supersede.py`'s two-file update (Task 4) guarantees each individual
  file is never torn by a mid-write crash, but does not guarantee the
  *pair* stays consistent if the process is killed between the two atomic
  writes -- true two-phase commit across files was explicitly scoped out
  (see the plan's Task 4 code comments).
- (carried over from the audit, still true) CHECK deliberately cannot
  prove prose, business rationale, or organizational claims; those remain
  human-review evidence.
- (carried over, still true) GitHub branch/tag protection is unavailable
  on the current private plan; revisit once the repository goes public --
  owner's stated plan is to do that after most audit findings are done and
  the version bumps to 1.0.0 (see project memory
  `project_v1_public_release_plan`).
