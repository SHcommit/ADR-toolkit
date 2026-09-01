# handoff.md

## Current task (2026-09-01)

**Both the Critical and High-priority hardening passes are done.** All 4
Critical-risk findings and 6 of 8 High-priority findings from
`docs/adr-toolkit-audit-report.md` are implemented, tested, and committed
on `feature/analyzing-adr-toolkit`. Full suite: 433 passed (up from 395 at
session start). Branch stays as-is per owner's explicit choice (not
merged/PR'd yet).

**Critical pass** (`docs/superpowers/plans/2026-09-01-critical-hardening.md`,
gitignored by convention, still on disk in this worktree):

1. `fc46830` feat: add atomic write and directory lock primitives
2. `49ede49` fix: make ADR creation race-free under concurrent invocation
3. `68bbd98` fix: make exception creation race-free under concurrent invocation
4. `cec7215` fix: make SUPERSEDE writes atomic and lock-protected
5. `c0ff907` fix: add ReDoS timeout guard to CHECK's author-supplied regex patterns
6. `7afdcd5` fix: escape ADR titles in generated README to prevent link injection
7. `11c8f4b` feat: add structured stderr logging with correlation IDs
8. `f0cbc86` docs: close out Critical hardening backlog items

**High-priority pass** (`docs/superpowers/plans/2026-09-01-high-priority-hardening.md`,
same gitignore convention):

1. `f92c8f5` fix: reject a --dir/--root that escapes the repository root
2. `52bd761` ci: measure and gate branch coverage at 85%
3. `305c836` feat: add typed result contracts and a mypy --strict CI gate
4. `46dd863` feat: add --diagnostic flag for per-invocation timing
5. `9708bb2` test: prove atomic_write_text survives a mid-write SIGKILL
6. `cff3d5e` feat: extract a shared adapter-manifest validator
7. (this commit) docs: close out High-priority hardening backlog items

`improvements.md` now has an empty `### Critical` section (removed
entirely) and a `### High` section containing only the 2 items explicitly
deferred to another worktree. The `### Medium` section is untouched and
unscheduled.

Notable things discovered mid-session, worth knowing if touching this code
again:

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
- Repo-root `scripts/` and `skills/adr-toolkit/scripts/` share the name
  `scripts` for Python's import system, and the latter (which has an
  `__init__.py`) wins whichever imports first in a pytest session. Any new
  file under repo-root `scripts/` must be loaded via
  `importlib.util.spec_from_file_location` in its tests, exactly like
  `scripts/sync_version.py` already does -- `scripts/adapter_sdk.py`
  follows the same pattern.
- Measured, not assumed: branch+statement coverage was 93.32% before
  adding the 85% CI gate; `mypy --strict` on `atomic_io.py`/`telemetry.py`
  had exactly 3 real errors, fixed as part of adding the `type-check` job.

## Scope for this worktree

Excluded here, being handled elsewhere -- do not touch:

- Domains 1 (core/plugin architecture) and 5 (governance/FSM) from the
  audit report -- already scored 72/80, mostly "no action needed" per the
  audit itself.
- Anything Antigravity (`agy`) adapter-related -- owner is working on this
  in another branch.
- Automatic version sync -- owner is working on this in another worktree;
  as a direct consequence, **do not touch `.github/workflows/release.yml`
  for any reason**. The remaining "(다른 워크트리 확인)" items in
  `improvements.md`'s `### High` section (supply-chain checksums/signing;
  the 8.4 auto-version-bump direction note) are deliberately left there
  for that other worktree.
- README prose (root README.md, `adapters/*/README.md` content) -- another
  worktree. Every fix in this session that touched adapter or index code
  was a code/generator fix, not README prose, and correctly stayed in
  scope here.

## Next step

Nothing is currently in flight. `improvements.md`'s remaining backlog --
the 2 other-worktree-flagged High items, plus the entire `### Medium`
section (JSON Schema single-source-of-truth, common error base class,
output contract schema freeze, parsing cache, bulk-ADR benchmark,
TTY-aware CLI output) -- is unscheduled. **Ask the owner before starting
any of it.** Every scope decision in this session (Critical-then-High
ordering, domain 1/5 exclusion, the other-worktree exclusions) was the
owner's explicit call in conversation, not something derivable from the
audit report alone.

## Verification

Full suite: `python3 -m pytest tests/unit tests/integration -v` -> 433
passed as of commit `cff3d5e` (432 on Windows, where the SIGKILL chaos
test in `test_atomic_io_chaos.py` is skipped).

CI now also runs a `type-check` job (`mypy --strict` on 3 modules) and
gates the `pytest` job's coverage at 85% -- both new since this session.

## Open risks

- The ReDoS guard is POSIX-only (`signal.SIGALRM`); Windows CI is
  unaffected but unguarded against catastrophic-backtracking patterns --
  a known, documented gap, not a regression introduced by this work.
- `supersede.py`'s two-file update guarantees each individual file is
  never torn by a mid-write crash, but does not guarantee the *pair*
  stays consistent if the process is killed between the two atomic writes
  -- true two-phase commit across files was explicitly scoped out.
- Every successful `create`/`exception`/`supersede` call now leaves a
  `.adr-toolkit.lock` (0-byte, dotfile) inside `docs/decisions/` and
  `docs/decisions/exceptions/` permanently -- intentional (the
  cross-process mutex), doesn't match `*.md`/`*.json` globs so nothing
  else picks it up, but worth knowing about if someone notices it in a
  repo diff.
- `core/contracts.py`'s TypedDicts currently model only a subset of one
  command's result shape (`CreateResult`) plus the shared error/base
  shapes -- extending coverage to the other 15 commands, and extending
  `mypy --strict` beyond the 3 fully-typed core modules into the command
  modules themselves (blocked on typing `argparse.Namespace` args), is
  future work, not started.
- (carried over from the audit, still true) CHECK deliberately cannot
  prove prose, business rationale, or organizational claims; those remain
  human-review evidence.
- (carried over, still true) GitHub branch/tag protection is unavailable
  on the current private plan; revisit once the repository goes public --
  owner's stated plan is to do that after most audit findings are done and
  the version bumps to 1.0.0 (see project memory
  `project_v1_public_release_plan`).
