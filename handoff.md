# handoff.md

## Current task

Release v1.1.0: VERSION bumped 1.0.1 → 1.1.0, manifests synced via
`scripts/sync_version.py`, `changelog.md` v1.1.0 section added. Release branch
`release/v1.1.0` off `develop` ready to merge into `master`; after merge, tag
`v1.1.0` will be pushed from `master` to trigger `.github/workflows/release.yml`.

## Touched files

- `skills/adr-toolkit/VERSION` — bumped to `1.1.0`.
- `skills/adr-toolkit/SKILL.md` — frontmatter `version: 1.1.0`.
- `.claude-plugin/plugin.json`, `adapters/gemini-cli/gemini-extension.json`,
  `adapters/antigravity/plugin.json` — `version` synced to `1.1.0`.
- `changelog.md` — moved the Unreleased block under a new `## v1.1.0 (2026-09-06)`
  heading summarizing the 31 commits accumulated since v1.0.1 (Cline adapter,
  CLINE.md/AGENTS.md harness entry, GitHub governance hardening, CI supply-chain
  hardening, ADR-0017, backlog items).
- `handoff.md` — this file.

## Why 1.1.0 (MINOR, not PATCH)

The 31 commits between v1.0.1 and this release include six `feat:` commits
(Cline CLI adapter, GitHub label taxonomy / labeler / dependabot / Issue Forms /
auto-triage). SemVer requires a MINOR bump for new backward-compatible
features; no breaking changes were identified, so MAJOR is not warranted and
PATCH would understate the surface change.

## Next step

1. Open PR `release/v1.1.0` → `master` (AGENTS.md: "Release branches merge
   into `master` and back into `develop`").
2. After CI passes (release.yml runs pytest + sync_version --check + tag ==
   VERSION), merge into `master`.
3. Back-merge `master` → `develop` (PR), per the git flow.
4. Tag `v1.1.0` from `master` and push — `release.yml` runs the full suite,
   verifies manifest versions against the tag, and publishes a GitHub
   Release (plus PyPI publish via Trusted Publisher, `continue-on-error`).
5. Delete the short-lived `release/v1.1.0` branch after merge.

## Verification

- `scripts/sync_version.py --check`: passes (VERSION, SKILL.md, and all
  4 manifests agree on 1.1.0; no untracked manifests).
- `changelog.md` reflects all 31 v1.0.1..develop commits.
- Working-tree state on `release/v1.1.0`: clean except for the version-sync +
  changelog/handoff commits.

## Open risks

- `pypa/gh-action-pypi-publish` remains `continue-on-error: true`, so the
  PyPI publish step can partially fail without failing the release job —
  tracked in `improvements.md`.
- Cline adapter is still "Manually verified against 3.0.61" only; the
  `harness-parity` CI job does not yet cover Cline — PR #36 logged this as a
  Medium backlog item to implement after v1.1.0 ships.
- Inherits prior Open risks (ruleset context sync post-merge, deferred
  project/milestone/stale automation).
