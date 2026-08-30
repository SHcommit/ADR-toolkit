# handoff.md

## Current task (2026-08-30)

ADR Toolkit `v0.2.0` minor-release implementation is complete, and the
`improvements.md` P1 backlog has been worked down to just the two items that
require the owner's own action. Everything else in P1 that was actionable by
an agent is done.

The work runs in the linked worktree `develop-2`. Its base is the current
`origin/develop` history plus the approved design commits:

- `7b9bb8c` — initial localization/readiness design
- `b69a784` — v0.2.0 release gates, repository config, CHECK confidence, and
  report separation

Baseline verification before implementation: `212 passed` on 2026-08-30.

## Touched since the last handoff

- `b9e0ec3` — hardened `sync_version.py`: silent drift when a tracked
  manifest loses its version key, a crash on a manifest path outside the
  repo root, and non-ASCII manifest content being escaped on write.
- `baa0987` — split the manifest version-drift CI check into its own job
  instead of running it on all 5 OS/Python matrix legs.
- `2f2a8de` — centralized ADR directory loading into
  `core.adr_directory.iter_adr_files`, shared by related/index/validate/check.
- `061d44e` — corrected `adapters/codex/README.md`: the documented
  install-time symlink step was unused by the actually-verified install path;
  removed it and explained why `.codex-plugin/plugin.json` is structural-only.
- `5d37bef` — made `SKILL.md`'s frontmatter description the canonical source,
  synced into every duplicating manifest by `sync_version.py`, fixing one
  real drift in `.claude-plugin/plugin.json`.
- `63c4c85` — formalized `--json` as a documented no-op (output is always
  JSON); added a regression test and fixed 3 docs that omitted the flag.
- `2c73af6` — promoted CHECK's confidence classification to a stable
  `confidence` field (`VERIFIED`/`VIOLATED`/`UNVERIFIABLE`) on every finding,
  computed from `kind` instead of left for the agent to re-derive from docs.
- `6e68b5d` — added a deterministic exception schema: `adr.py exception`
  validates and records `owner`/`reason`/`scope`/`expiry`/`adr_id`/`rule_id`
  as `docs/decisions/exceptions/EXC-NNNN.json`; CHECK annotates a matching,
  non-expired exception onto a finding without ever suppressing or
  downgrading it.

Latest local verification on 2026-08-30:

- `python3 -m pytest -q` → `327 passed`, exit 0
- `python3 scripts/sync_version.py --check` → exit 0
- `git status --short` → clean

The detailed v0.2.0 evidence and maturity assessment are in
`docs/adr-toolkit-v0.2.0-readiness-report.md` (not re-verified against the
latest commits above — re-run its evidence commands before treating its
GO/NO-GO judgment as current); post-release governance is kept separate in
`docs/enterprise-adoption.md`, whose §8 "다음 구현 후보" now reflects items 1,
3, and 4 as done.

## Next step

Two `improvements.md` P1 items remain, both requiring the owner, not an
agent:

- **Codex metadata compatibility** — deliberately deferred by the owner
  (2026-08-30); revisit only when asked.
- **Stale remote branch cleanup** (`origin/SHcommit/feat-plan-adr-toolkit`,
  `origin/feat/adr-toolkit-mvp-implement`) — needs the owner's explicit
  deletion approval; not attempted.

Beyond that, the only remaining work is the P0 release gate: open the final
PR, get required CI green, get the owner's approval for the v0.2.0 version
bump, merge through a release branch, and verify the tag lands on the
intended `master` commit. `develop-2` has not been pushed to `origin` yet
(no upstream branch configured) — the owner has said they'll handle the
public-repository transition themselves later, and PR/push have not been
authorized in this session.

`project-roadmap.md` was reviewed end to end: every item there is explicitly
gated on usage evidence or a separate design decision that doesn't exist yet
— nothing there is actionable now.

## Open risks

- Catalog structure is deterministic, but terminology still benefits from
  native-speaker review in each supported language.
- CHECK deliberately cannot prove prose, business rationale, or organizational
  claims; those remain human-review evidence. The new exception mechanism
  extends this: an exception is recorded and annotated, never a silent pass.
- GitHub protection is intentionally unavailable in the current private plan;
  configure and API-verify it after the repository becomes public (owner's
  own follow-up, not scheduled here).
- Version bump, release branch, push, and tag are not authorized by this task.
