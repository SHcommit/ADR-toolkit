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

**Low-priority follow-up** (3 of 4 audit-report Low items):
`0307a1c` allows `proposed -> deprecated` and documents `constraints:`
block review in `CONTRIBUTING.md`; `9a44342` adds `core/constraints.lint()`
and wires it into `create.py` (always) and `status.py` (only on
transition to `accepted`, since that's the status CHECK actually enforces
constraints against) so a typo surfaces at authoring time instead of only
at CHECK time -- `CreateResult`/`StatusResult` gained a `warnings` field
to match. The 4th item (Antigravity in `harness-parity`) stays open,
blocked on `agy` getting a public package registry.

**Windows ReDoS gap closed** (`26021a9`, promoted from this file's own
Open Risks below, not a numbered backlog item): `core/constraints.py`
statically rejects nested-quantifier `pattern` values (`(a+)+`-shaped) at
parse time for `forbidden_import`/`dependency_forbidden` rules -- a
string-level check that works the same on every OS, unlike
`rules/conflict.py`'s SIGALRM-based runtime timeout (POSIX-only). Verified
against the real dogfooded `ADR-0011` constraints block (no false
positive) and that a rejected pattern never reaches `re.compile()`.
Heuristic, not a full ReDoS detector -- alternation-based shapes like
`(a|a)*` remain uncaught, noted in the code.

**Backlog reconciliation** (docs-only, no commit yet as of writing this):
the owner pointed out that PR #6 (`feature/agy-plugin-implements-2`) and
PR #7 (`feature/add-githooks`) -- the "다른 워크트리" that the High
section's 2 items were deferred to -- are both already merged into
`origin/develop` and pulled into this branch. Re-checked both items
against the actual current code rather than assuming: the 8.4
auto-version-direction review is genuinely done (no conflict found,
moved to `## Done`) and removed from Open; the supply-chain signing item
is genuinely still unimplemented (confirmed by reading `release.yml`) and
stays Open, just with the stale "다른 워크트리 확인" framing removed.
Also re-verified the Antigravity/harness-parity Low item is still
correctly blocked (agy still has no public registry, per
`adapters/antigravity/README.md`) -- not everything merged from that
worktree closes every item tied to it.

**Concurrent work (owner's own coordination, not this session's):** the
owner assigned `improvements.md`'s "도입 지표 수집 스크립트"
(adoption-metrics script, from `docs/enterprise-adoption.md` §7) to a
**Codex session running in this same worktree/branch** in parallel with
this session, specifically because it's a new-file-only task with no
overlap against the files this session was touching. If you see an
uncommitted or newly-committed `scripts/adoption_metrics.py` (or
similarly named) plus a matching test file that you don't recognize
authoring, that's Codex's work landing -- don't revert it, and check
`improvements.md`'s enterprise-adoption.md sub-group for whether it's
already been checked off before restarting it.

All 3 plan files are gitignored by convention (`docs/superpowers/plans/`)
but still on disk in this worktree.

`improvements.md` now has: an empty `### Critical` section, a `### High`
section containing only the 2 items explicitly deferred to another
worktree, and a `### Medium` section with exactly one item -- the
parsing-result cache, marked **declined with rationale** (see below). It
also has a **Low-priority tier with two sourced sub-groups**, added at
the owner's request:
- 4 items pulled from `docs/adr-toolkit-audit-report.md`'s own 🟢 Low-risk
  findings (the ones that actually still need action -- most of the 8
  Low findings in that report were "no action needed" or already resolved
  by this session's work or the `origin/develop` merge, e.g. its
  Conventional-Commits PR title suggestion is now the merged-in
  `pr-title-check` CI job).
- 4 items pulled from `docs/enterprise-adoption.md` §8 (a separate
  governance/adoption-maturity report) -- see that file's notes below for
  why most of those are precondition-gated rather than pure code tasks.

(An earlier pass in this session mistakenly added only the
enterprise-adoption.md half when asked to pull Low items "from the
report" -- corrected once the ambiguity was pointed out.)

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

- Domains 1 (core/plugin architecture) and 5 (governance/FSM) from the
  audit report -- still out of scope, already scored well.
- **The Antigravity (`agy`) adapter and automatic-version-sync worktree
  no longer exists as a separate concern** -- its work merged via GitHub
  PR #6/#7 into `origin/develop`, which this branch pulled in (`0a0db8a`).
  Re-verified against the actual merged code (not assumed): confirmed
  `scripts/sync_version.py`/`release.yml` still do manual-only version
  bumps (no conflict with the audit's recommendation -- that review item
  is now closed, see `improvements.md`'s `## Done`), and confirmed
  `.github/workflows/release.yml` still has no supply-chain checksum/
  signing step (that item is now open and startable in this worktree,
  not blocked by a concurrent editor anymore -- but touches the release
  pipeline, so confirm with the owner before starting).
- README prose (root README.md, `adapters/*/README.md` content) --
  still another worktree's; every fix across all passes that touched
  adapter or generator code was a code fix, not README prose.
- **Do not touch what the parallel Codex session is doing** (the
  adoption-metrics collector -- already 4 commits in as of `45b3472`,
  see below). Don't revert, refactor, or duplicate its work.

## Next step (for a new session picking this up cold)

**One real, startable item exists in `improvements.md`'s `## Open`**:
supply-chain checksums/signing for `.github/workflows/release.yml`
(§2.2 2.2) -- verified not implemented, no longer blocked by a separate
worktree, but touches the release pipeline so confirm with the owner
before starting. Everything else is either precondition-gated or the
parallel Codex session's. Concretely:

1. `improvements.md`'s `### High` now has exactly 1 item (the
   supply-chain one above) -- startable with owner confirmation, since
   it modifies `release.yml`.
2. `improvements.md`'s `### Low` → audit-report sub-group has exactly 1
   item left (Antigravity in `harness-parity`), re-verified against
   `adapters/antigravity/README.md` and still blocked on an external fact
   (agy has no public package registry) -- don't start it.
3. `improvements.md`'s `### Low` → enterprise-adoption.md sub-group: check
   whether the Codex session's adoption-metrics work has been checked off
   before assuming it's still open (as of this note it's implemented --
   `9a0de45`..`45b3472` -- but not yet reflected in `improvements.md`
   since this session was told not to touch that item's bookkeeping). The
   other 3 items there remain precondition-gated (repository going
   public, 2+ maintainers, 2+ repositories) -- **not pure code tasks**.
4. If the user says "continue" / "다음 작업 진행해줘" without naming a
   task: the supply-chain item is the one thing to offer; otherwise ask
   what's next rather than inventing scope.
5. If the user wants to finish this branch (merge to `develop` / open a
   PR): that decision was deferred every time it came up this session
   (owner chose "keep as-is" each time) -- ask again fresh, don't assume
   the answer carried forward. This branch already includes the merged
   `origin/develop` history, so a future merge/PR back to `develop`
   should be a clean fast-forward-friendly merge.
6. If the user references a new audit finding or a fresh problem: that's
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

`python3 -m pytest tests/unit tests/integration -v` -> 518 passed as of
commit `26021a9` (395 at session start -> 465 before the `origin/develop`
merge -> 469 after merging in develop's own new tests -> 479 after the
Low-priority follow-up work -> 518 current, which also includes the
parallel Codex session's adoption-metrics tests landing in this branch).
CI now also runs `type-check` (`mypy --strict`), `examples-drift` (from
develop), and `pr-title-check` (from develop) jobs alongside the existing
`pytest` (now coverage-gated at 85%), `version-drift`, and
`harness-parity` jobs.

## Open risks

- ~~The ReDoS guard is POSIX-only...~~ **Mitigated (`26021a9`)**: the
  runtime SIGALRM timeout is still POSIX-only, but a static
  nested-quantifier check in `core/constraints.py` now rejects the most
  common ReDoS shape at parse time on every platform, so Windows is no
  longer completely unguarded. Not a full ReDoS detector -- alternation-
  based patterns (`(a|a)*`-shaped) still rely on the POSIX-only runtime
  guard and remain unmitigated on Windows.
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
