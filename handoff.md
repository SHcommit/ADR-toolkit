# handoff.md

## Current task

Cline CLI adapter harness-parity CI coverage gap — logged as a Medium backlog
item. The Cline adapter is currently "Manually verified against Cline CLI 3.0.61"
only; the `harness-parity` CI job does not yet install Cline and exercise it on
push/PR. Codex, Gemini, and Antigravity adapters are already automated.

## Touched files

- `improvements.md` — added Medium item "harness-parity CI에 Cline CLI 편입"
  with prerequisites (npm package name/version pin, install-path verification,
  `preflight`/`init`/`validate` `ok:true` checks).
- `project-roadmap.md` — added "Automate the Cline CLI adapter install-and-run
  verification — Backlog." entry under "Harness parity".
- `changelog.md` — one Unreleased line recording the backlog item.
- `handoff.md` — this file (current task + next step).

## Diagnosis (for the next session)

Cline CLI 3.0.61 is installed at `/Users/yangseunghyeon/.npm-global/bin/cline`.
`cline skill list` from the repo root shows `adr-toolkit` as a **Project Skill**
(source: local, from `~/Development/ADR-toolkit/skills/adr-toolkit`) — i.e. the
repo's own `skills/` directory is auto-detected, NOT a global install.
`cline plugin list` is empty and `~/.agents/skills/` is empty, confirming the
adapter is README-only (no Cline TS plugin) and nothing was globally installed.

## Next step

1. (Optional, for personal use) `cline skill add SHcommit/ADR-toolkit --global -y`
   to make the skill available outside this repo.
2. (Future PR) Implement the Medium backlog item: confirm `cline`'s npm package
   name/version-pin, add a Cline step to `.github/workflows/test.yml`
   `harness-parity` job, verify `cline skill add ... --global --yes`, and run
   `preflight`/`init`/`validate` from the installed snapshot on each push/PR.
   Open a `feature/*` branch per the git flow and merge into `develop` via PR.

## Verification

- `tests/unit/test_cline_adapter.py`: pass (doc-only change, code unaffected).
- `ruff check .`: to be confirmed below.

## Open risks

- Until the Cline harness-parity step lands, Cline CLI/ClinePass version drift
  (e.g. `cline skill add` path or `~/.agents/skills/` location changing) will
  not be caught by CI. The `adapters/cline/README.md` verification block stays
  pinned to 3.0.61 until automated.
- Inherits the prior Open risks from the OSS governance hardening handoff
  (ruleset context sync, `continue-on-error` PyPI publish, deferred
  issue/PR automation).
