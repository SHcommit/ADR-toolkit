# handoff.md

## Current task (2026-09-01)

**The Critical, High-priority, and Medium-priority hardening passes are
all done.** Every findable item from `docs/adr-toolkit-audit-report.md`
that was in scope for this worktree is implemented, tested, and
committed on `feature/analyzing-adr-toolkit`. Branch stays as-is per
owner's explicit choice (not merged/PR'd yet).

**`origin/develop` was merged into this branch** after diverging
significantly: it now includes the `v0.2.1` release (examples redesign,
Korean docs suite, `scripts/verify_examples.py` verification pipeline),
the Antigravity (`agy`) plugin manifest enhancements, `.githooks/pre-push`,
and a Conventional-Commits PR title CI check -- all from other
worktrees/branches, per this repo's own scope split. The merge touched 3
files with real conflicts, resolved as follows:
- `changelog.md`: their `v0.2.1` release cut moved the old "Unreleased"
  bullets into a `## v0.2.1 (2026-08-31)` section and started a fresh
  "Unreleased" for post-release work; this branch's 16 hardening bullets
  were genuinely-still-unreleased, so they were merged into that same
  fresh "Unreleased" section alongside their 7 new bullets.
- `tests/unit/test_antigravity_adapter.py`: both sides added a new test
  function (this branch's shared-validator test, their symlink-layout
  test) -- kept both. Their new test called `pytest.skip(...)` without
  `import pytest`; added the import as part of resolving this, since
  otherwise a symlink-unsupported environment would hit `NameError`
  instead of skipping cleanly.
- `handoff.md` (this file): kept this branch's detailed history, folded
  in a short note (this paragraph) about what merged in from develop.
  `.github/workflows/test.yml` auto-merged cleanly (both sides' new CI
  jobs coexist: `pytest`+coverage, `type-check`, `examples-drift`,
  `pr-title-check`, `harness-parity`, `version-drift`).

**Critical pass** (`docs/superpowers/plans/2026-09-01-critical-hardening.md`):
`fc46830` atomic write + lock primitives, `49ede49` create.py race fix,
`68bbd98` exception.py race fix, `cec7215` supersede.py atomic writes,
`c0ff907` ReDoS guard, `7afdcd5` README link-injection fix, `11c8f4b`
structured logging, `f0cbc86` docs closeout.

**High-priority pass** (`docs/superpowers/plans/2026-09-01-high-priority-hardening.md`):
`f92c8f5` path escape guard (initial), `52bd761` coverage CI gate,
`305c836` mypy strict gate + contracts.py, `46dd863` `--diagnostic` flag,
`9708bb2` SIGKILL chaos test, `cff3d5e` adapter manifest validator,
`9a974b7` docs closeout.

**Medium-priority pass** (`docs/superpowers/plans/2026-09-01-medium-priority-hardening.md`):
`41998a2` common `AdrToolkitError` base + fixed the path-escape gap the
High pass left behind (all 7 `resolve_from_root` call sites now catch
it), `e3d592b` schema-drift detection test (no `jsonschema` dependency
added -- see rationale in that commit), `2933575` extended
`contracts.py` to cover CHECK, `d7368f6` bulk-ADR performance sanity
check, `c3ed01d` TTY-only stderr summary line, `77ce206` docs closeout.

**Follow-up** (owner asked to continue per `improvements.md`/`handoff.md`
after the Medium pass): `1df6066` extended `core/contracts.py` to cover
the remaining 14 commands (was 2/16, now 16/16) -- each shape read from
the actual `run()` return statements, not guessed, and spot-checked
against real error-path output for `status`/`supersede` too.

All 3 plan files are gitignored by convention (`docs/superpowers/plans/`)
but still on disk in this worktree.

`improvements.md` now has: an empty `### Critical` section, a `### High`
section containing only the 2 items explicitly deferred to another
worktree, and a `### Medium` section with exactly one item -- the
parsing-result cache, marked **declined with rationale** (see below). It
also has a **Low-priority tier**, added at the owner's request, pulled
from `docs/enterprise-adoption.md` §8 -- see that section below for why
most of those items are precondition-gated rather than pure code tasks.

**One Medium item was declined, not silently skipped:** the audit's
`functools.lru_cache` suggestion for parsing-result caching provides zero
real benefit for this CLI -- it's a fresh process per invocation (no
shared memory across separate `python adr.py X` calls, which was the
actual scenario the audit worried about), and no single command
internally re-parses the same file more than once. A cache that would
actually help (persistent, on-disk, mtime-keyed, shared across process
invocations) is a much bigger, staleness-risk-bearing feature
disproportionate to real ADR counts. Recorded in `improvements.md` with
this rationale.

Notable things discovered mid-session, worth knowing if touching this
code again:

- `create.py`/`exception.py`: naively wrapping everything in
  `adr_directory_lock` made *dry runs* (and, for `exception.py`,
  *schema-validation failures*) create the directory + lock file as a
  side effect, breaking existing tests. Fixed by keeping preview/
  validation paths outside the lock.
- `supersede.py`: two existing tests monkeypatched `Path.write_text`
  directly; retargeted to `supersede.atomic_io.atomic_write_text` once
  writes moved through it.
- Repo-root `scripts/` and `skills/adr-toolkit/scripts/` share the import
  name `scripts` -- anything new under repo-root `scripts/` needs
  `importlib.util.spec_from_file_location` in its tests, like
  `scripts/sync_version.py` and `scripts/adapter_sdk.py` both do.
- `PathEscapesRootError` was added in the High-priority pass but never
  actually caught anywhere until the Medium pass noticed and fixed it --
  every *other* domain exception in this codebase is caught explicitly at
  its call site, so an uncaught one was an inconsistency worth closing.
- Measured, not assumed: branch+statement coverage was 93.32% before the
  85% CI gate; `mypy --strict` had exactly 3 real errors on the 2
  pre-existing typed modules; a bare `dict` field in a TypedDict fails
  `mypy --strict`'s `type-arg` check -- use `Dict[str, Any]`.

## Scope for this worktree

Excluded here, being handled elsewhere -- do not touch:

- Domains 1 (core/plugin architecture) and 5 (governance/FSM) from the
  audit report.
- Anything Antigravity (`agy`) adapter-related -- another branch (now
  merged into `develop` as of this session's merge -- see above).
- Automatic version sync -- another worktree; **do not touch
  `.github/workflows/release.yml` for any reason.** The 2 remaining
  "(다른 워크트리 확인)" items in `improvements.md`'s `### High` section
  are deliberately left there for that other worktree.
- README prose (root README.md, `adapters/*/README.md` content) --
  another worktree. Every fix across all 3 passes that touched adapter or
  generator code was a code fix, not README prose.

## Next step (for a new session picking this up cold)

**Nothing is currently in flight in this worktree's own scope**, but
`improvements.md` now carries a **Low-priority tier** (added this
session from `docs/enterprise-adoption.md` §8) that a future session can
pick up -- see that file's `### Low` section for the exact items and
their preconditions. Concretely:

1. `improvements.md`'s `## Open` → `### High` still has exactly 2 items
   left, both flagged `(다른 워크트리 확인)` -- still someone else's.
   Do not start them here.
2. `improvements.md`'s new `### Low` section has items sourced from
   `docs/enterprise-adoption.md`. Read that section's notes carefully
   before starting any of them: most are **not pure code tasks** --
   they're gated on real-world preconditions (the repository actually
   going public, 2+ repositories existing) that no amount of local
   editing satisfies. Don't "implement" a GitHub ruleset change by
   writing a script that doesn't actually call the GitHub API against a
   real public repo, and don't build multi-repo tooling against a
   single-repo reality.
3. If the user says "continue" / "다음 작업 진행해줘" without naming a
   task: check `improvements.md`'s `### Low` section first (that's the
   one open, actionable-albeit-constrained tier); don't restart
   already-declined work (parsing-result cache) or reach into another
   worktree's High items without being told to.
4. If the user wants to finish this branch (merge to `develop` / open a
   PR): that decision was deferred every time it came up this session
   (owner chose "keep as-is" each time) -- ask again fresh, don't assume
   the answer carried forward. Note this branch now includes the merged
   `origin/develop` history (see above), so a future merge/PR back to
   `develop` should be a clean fast-forward-friendly merge, not a repeat
   of this session's conflict resolution.
5. If the user references a new audit finding or a fresh problem: that's
   genuinely new work -- use the same pattern this session established
   (writing-plans -> executing-plans, TDD, one commit per task, verify
   real test/mypy output before each commit) rather than skipping
   straight to edits.

Every scope decision across all passes (Critical-then-High-then-Medium
ordering, domain 1/5 exclusion, the other-worktree exclusions, the
parsing-cache decline) was the owner's explicit call or a judgment call
made and explained in-session, not something derivable from the audit
report alone -- see `improvements.md`'s `## Done` for the full rationale
on each.

## Verification

Full suite before the `origin/develop` merge:
`python3 -m pytest tests/unit tests/integration -v` -> 465 passed. Re-run
this after the merge to get the current combined count (develop's new
`tests/integration/test_examples.py` and expanded
`test_antigravity_adapter.py` add more). CI now also runs `type-check`
(`mypy --strict`), `examples-drift` (from develop), and `pr-title-check`
(from develop) jobs alongside the existing `pytest` (now coverage-gated
at 85%), `version-drift`, and `harness-parity` jobs.

## Open risks

- The ReDoS guard is POSIX-only (`signal.SIGALRM`); Windows CI is
  unaffected but unguarded -- a known, documented gap.
- `supersede.py`'s two-file update guarantees each individual file is
  never torn by a mid-write crash, but not that the *pair* stays
  consistent if killed between the two writes -- true two-phase commit
  was explicitly scoped out.
- Every successful `create`/`exception`/`supersede` call leaves a
  `.adr-toolkit.lock` (0-byte dotfile) permanently inside
  `docs/decisions/` and `docs/decisions/exceptions/` -- intentional (the
  cross-process mutex), doesn't match `*.md`/`*.json` globs.
- `core/contracts.py` now covers all 16 commands' result shapes, but
  extending `mypy --strict` beyond the fully-typed core modules into the
  command modules themselves (blocked on typing `argparse.Namespace`
  args) is still future work.
- (carried over from the audit, still true) CHECK deliberately cannot
  prove prose, business rationale, or organizational claims.
- (carried over, still true) GitHub branch/tag protection is unavailable
  on the current private plan; revisit once the repository goes public
  after most audit findings are done and the version bumps to 1.0.0 (see
  project memory `project_v1_public_release_plan`) -- this is also the
  precondition blocking `improvements.md`'s new Low-priority item #1
  (`docs/enterprise-adoption.md`'s public-transition ruleset gate).
