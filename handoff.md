# handoff.md

## Current task (2026-08-30)

ADR Toolkit `v0.2.0` minor-release implementation is complete. The
`improvements.md` P1 backlog has been fully worked down — every item that
was actionable by an agent is done, and the two that weren't (Codex
metadata compatibility, stale branch cleanup) were resolved with the
owner's decision/approval. This session's own design decisions have been
dogfooded as ADR-0007..0010.

The work runs in the linked worktree at `/Users/yangseunghyeon/orca/workspaces/ADR-toolkit/develop-2`
(directory name unchanged; the branch itself was renamed). Its base is the
current `origin/develop` history plus the approved design commits:

- `7b9bb8c` — initial localization/readiness design
- `b69a784` — v0.2.0 release gates, repository config, CHECK confidence, and
  report separation

Baseline verification before implementation: `212 passed` on 2026-08-30.

**Branch renamed**: `develop-2` → `feature/v0.2.0-multilingual-and-check-confidence`
(local rename only; not yet pushed, no upstream configured).

## Touched since the last handoff

- `c995904` — closed the Codex metadata compatibility item as not
  applicable: `quick_validate.py` belongs to Codex's local skill-creator
  tool, never the actual plugin install path (independently re-verified).
- `b1a4ec5` — deleted the two stale remote branches
  (`origin/SHcommit/feat-plan-adr-toolkit`,
  `origin/feat/adr-toolkit-mvp-implement`); both were fully merged into
  `origin/develop` with no open PR referencing either.
- `2fa6d67` — recorded ADR-0007..0010 for this session's own design
  decisions, scored via `adr.py significance` before writing:
  - ADR-0007 (10, recommended) — CHECK's `kind`→`confidence` mapping
    promoted to a stable output field.
  - ADR-0008 (12, recommended) — deterministic CHECK policy exceptions,
    schema-validated and annotate-only, never suppressing a violation.
  - ADR-0009 (7, recommended) — `--json` is a documented no-op; CLI output
    is always JSON.
  - ADR-0010 (4, optional) — Codex `quick_validate.py` incompatibility is
    not this project's problem, with the verification evidence recorded.

(Earlier in this session — still current, not re-listed in detail: `b9e0ec3`
sync_version.py hardening, `baa0987` CI dedup, `2f2a8de` ADR directory
centralization, `061d44e` Codex adapter doc fix, `5d37bef` manifest
description ownership, `63c4c85` `--json` implementation, `2c73af6` CHECK
confidence field implementation, `6e68b5d` exception schema implementation
— ADR-0007..0010 above are the *rationale records* for the last three of
these.)

Latest local verification on 2026-08-30:

- `python3 -m pytest -q` → `327 passed`, exit 0
- `python3 scripts/sync_version.py --check` → exit 0
- `adr.py validate --dir docs/decisions` → `checked: 10`, no errors
- `adr.py index --dir docs/decisions` regenerated cleanly
- `git status --short` → clean

The detailed v0.2.0 evidence and maturity assessment are in
`docs/adr-toolkit-v0.2.0-readiness-report.md` (not re-verified against the
commits since it was written — re-run its evidence commands before treating
its GO/NO-GO judgment as current); post-release governance is kept separate
in `docs/enterprise-adoption.md`, whose §8 "다음 구현 후보" now reflects
items 1, 3, and 4 as done.

## Next step

`improvements.md` has exactly one open item left: the P0 release gate. Open
the final PR (from `feature/v0.2.0-multilingual-and-check-confidence`
against `develop`), get required CI green, get the owner's approval for the
v0.2.0 version bump (`skills/adr-toolkit/VERSION` is still `0.1.0`), merge
through a release branch, and verify the tag lands on the intended `master`
commit. The branch has not been pushed to `origin` yet (no upstream
configured) — the owner has said they'll handle the public-repository
transition themselves later, and push/PR have not been authorized in this
session.

`project-roadmap.md` was reviewed end to end: every item there is explicitly
gated on usage evidence or a separate design decision that doesn't exist yet
— nothing there is actionable now.

An open, undecided idea from this session: measuring how much LLM-token
input/output the deterministic core saves an agent versus doing the same
work by reading/writing everything by hand (e.g. CHECK returning a
structured finding instead of the agent scanning a full diff). Discussed but
deliberately deferred — no scope or destination (new doc section vs.
benchmarking script) has been decided.

## Open risks

- Catalog structure is deterministic, but terminology still benefits from
  native-speaker review in each supported language.
- CHECK deliberately cannot prove prose, business rationale, or organizational
  claims; those remain human-review evidence. The exception mechanism
  extends this: an exception is recorded and annotated, never a silent pass.
- GitHub protection is intentionally unavailable in the current private plan;
  configure and API-verify it after the repository becomes public (owner's
  own follow-up, not scheduled here).
- Version bump, release branch, push, and tag are not authorized by this task.
