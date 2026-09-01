# handoff.md

## Current task (2026-09-01)

**The Critical, High-priority, and Medium-priority hardening passes are
all done.** Every findable item from `docs/adr-toolkit-audit-report.md`
that was in scope for this worktree is implemented, tested, and
committed on `feature/analyzing-adr-toolkit`. Full suite: 452 passed (up
from 395 at session start). Branch stays as-is per owner's explicit
choice (not merged/PR'd yet).

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
parsing-result cache, marked **declined with rationale** (see below).
Nothing else is open in this worktree's scope.

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
- Anything Antigravity (`agy`) adapter-related -- another branch.
- Automatic version sync -- another worktree; **do not touch
  `.github/workflows/release.yml` for any reason.** The 2 remaining
  "(다른 워크트리 확인)" items in `improvements.md`'s `### High` section
  are deliberately left there for that other worktree.
- README prose (root README.md, `adapters/*/README.md` content) --
  another worktree. Every fix across all 3 passes that touched adapter or
  generator code was a code fix, not README prose.

## Next step

Nothing is currently in flight, and nothing is left unscheduled inside
this worktree's scope -- `improvements.md`'s only remaining Open items
are the 2 explicitly deferred to another worktree. If a future session is
asked to "continue per improvements.md/handoff.md" again and finds
nothing left there, that is the correct, complete state -- don't invent
new work; ask the owner what's next. Every scope decision across all
passes (Critical-then-High-then-Medium ordering, domain 1/5 exclusion,
the other-worktree exclusions, the parsing-cache decline) was the owner's
explicit call or a judgment call made and explained in-session, not
something derivable from the audit report alone.

## Verification

Full suite: `python3 -m pytest tests/unit tests/integration -v` -> 465
passed as of commit `1df6066` (464 on Windows, where the SIGKILL chaos
test is skipped).

CI now also runs a `type-check` job (`mypy --strict`) and gates the
`pytest` job's coverage at 85%.

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
  project memory `project_v1_public_release_plan`).
