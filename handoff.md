# handoff.md

## Current task (2026-09-02)

**Shipped as v0.3.1.** Every findable item from
`docs/adr-toolkit-audit-report.md` that was in scope for this worktree is
implemented, tested, and released. `feature/analyzing-adr-toolkit` merged
into `develop` (PR #8, after CI caught and this session fixed a real
Windows/Python-3.9-only path-escape bug), then `develop` → `release/0.3.0`
→ `master` (PR #9). The `v0.3.0` tag's release run failed at the
attestation step (GitHub rejects attestation for a private repo, only
discoverable against a real tag push) and never published a release; a
hotfix (PR #10) guarded that step on repo visibility and bumped to
v0.3.1, which released successfully. `master` was merged back into
`develop` (PR #11); both branches are identical. All short-lived branches
were deleted after merge. This session's own decisions are recorded as
ADR-0012..0016 (`docs/decisions/`), created via `adr.py create` itself
rather than a separate worklog doc.

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

**Supply-chain attestation completed** (`18d4662`, the item the
"Backlog reconciliation" note below left open): `.github/workflows/release.yml`
now packages `skills/adr-toolkit/` into a version-named tarball, SHA-256
checksums it, and generates a Sigstore-backed GitHub Artifact Attestation
(`actions/attest-build-provenance@v2`, keyless/OIDC -- no private key to
manage or rotate) for it; both the tarball and checksum are attached to
the GitHub Release. Chose this over signing the git tag itself because
tags in this project are created locally by a human before the triggering
push (`AGENTS.md`'s documented release process), so CI has no way to
retroactively sign an already-pushed tag -- attestation instead ties
provenance to the exact commit the tag points to. `SECURITY.md` gained a
"Verifying a Release" section (`sha256sum -c` + `gh attestation verify`)
that also clarifies git-clone/adapter-install paths verify via Git/GitHub
history, not this archive. Full option analysis:
`docs/worklogs/2026-09-01-supply-chain-attestation.md`. Verified: YAML
syntax, full test suite green (541 passed, no regressions) -- the actual
OIDC attestation issuance/verification flow itself can only be confirmed
end-to-end on a real `v*` tag push, not locally.

**Adoption metrics follow-up completed:**

- [x] `9a0de45`..`f814d64` add the design, JSON-only
  `scripts/adoption_metrics.py` collector, focused tests, review fixes, and
  final verification records.

The collector calculates all five metrics from `docs/enterprise-adoption.md`
§7 using ADR/exception data plus optional local Git, explicit JSONL event and
CHECK snapshot files, and GitHub review evidence. Incomplete evidence is
reported through coverage, availability, and warning fields rather than being
silently treated as complete data.

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
  is now closed, see `improvements.md`'s `## Done`); the supply-chain
  checksum/signing gap this note originally flagged is also closed now
  (`18d4662`, GitHub Artifact Attestation -- see `## Done` above).
- README prose (root README.md, `adapters/*/README.md` content) --
  still another worktree's; every fix across all passes that touched
  adapter or generator code was a code fix, not README prose.
- The adoption-metrics collector is complete; future changes should preserve
  its provider-neutral evidence contracts and JSON-only stdout behavior.

## Next step (for a new session picking this up cold)

**Everything is merged, released, and cleaned up.** `develop` and
`master` are identical (`git diff origin/develop origin/master` is
empty); `v0.3.1` is the live GitHub Release
(https://github.com/SHcommit/ADR-toolkit/releases/tag/v0.3.1); no
short-lived branches remain. `improvements.md`'s `### High` and
`### Medium` are empty. Concretely, for a new session:

1. There is no ready-to-start backlog item. `improvements.md`'s
   `### Low` → audit-report sub-group has exactly 1 item left
   (Antigravity in `harness-parity`), still blocked on `agy` having no
   public package registry -- don't start it without re-verifying that
   fact changed. Its enterprise-adoption.md sub-group has 3
   precondition-gated items (repository going public, 2+ maintainers,
   2+ repositories) -- **not pure code tasks**.
2. A GitHub Wiki was considered and explicitly declined for now (owner
   asked "위키 같은 거 만드는 게 좋을까?") -- this project's docs-as-ADRs
   model (versioned, reviewed, tied to releases) already covers the
   need; a wiki would fragment that. Revisit only once the repo is
   public and community-contributed FAQ/tutorial content that doesn't
   fit README/examples actually starts accumulating.
3. If the user says "continue" / "다음 작업 진행해줘" without naming a
   task: say there is no ready-to-start backlog item and ask what's
   next (a new audit finding, a precondition that's now met, or
   something else) rather than inventing scope.
4. If the user references a new audit finding or a fresh problem: that's
   genuinely new work -- use the same pattern this session established
   (writing-plans -> executing-plans, TDD, one commit per task, verify
   real test/mypy output before each commit) rather than skipping
   straight to edits.
5. This repository enforces a local `.githooks/pre-push` hook that
   blocks direct pushes to `develop`/`master` (no GitHub branch
   protection is configured -- the repo is private, which is a GitHub
   Pro-only feature -- so the hook is the *only* enforcement). Any future
   merge into either branch needs a short-lived branch + `gh pr create`
   + `gh pr merge`, not a direct push. A release still follows Git Flow:
   tag from `master` only, after a `release/*` (or `hotfix/*` for a
   post-release bug) branch merges in via PR.

Every scope decision across all passes (Critical-then-High-then-Medium
ordering, domain 1/5 exclusion, the other-worktree exclusions, the
parsing-cache decline) was the owner's explicit call or a judgment call
made and explained in-session, not something derivable from the audit
report alone -- see `improvements.md`'s `## Done` for the full rationale
on each.

## Verification

`python3 -m pytest tests/unit tests/integration -q` -> 541 passed after the
adoption-metrics collector and review fixes. `mypy --strict` over the three CI
target modules, examples verification, version-sync verification, collector
compilation, and `git diff --check` also pass.
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
