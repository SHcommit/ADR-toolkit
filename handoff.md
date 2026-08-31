# handoff.md

## Current task (2026-08-31)

Public-readiness and ADR navigation graph work is implemented on branch
`feature/project-roadmap-implements` in:

`/Users/yangseunghyeon/orca/workspaces/ADR-toolkit/develop`

Latest commits:

- `8f0343e feat: add ADR relationship graph exports`
- ADR-0011 work is in progress in the working tree and should be committed
  after final verification.

Implemented in this session:

- `adr.py graph --format mermaid|svg|both` exports deterministic Mermaid and
  Python-rendered SVG artifacts.
- `adr.py index` embeds a GitHub-renderable Mermaid relationship graph in the
  generated decision log.
- Public repository hygiene docs were added:
  `CONTRIBUTING.md`, `SECURITY.md`, and `.github/PULL_REQUEST_TEMPLATE.md`.
- `project-roadmap.md` now lists only remaining unscheduled work; completed
  graph/search/public-doc items were removed.
- ADR-0011 records the Mermaid/SVG graph and public readiness decision.

## Next step

Commit the ADR-0011 follow-up after verification. Then open or update a PR for
`feature/project-roadmap-implements` into `develop`.

The broader `v0.2.0` release gate still needs separate explicit owner approval
for each step:

1. Merge the PR into `develop`.
2. Cut a `release/*` branch into `master` and back into `develop`, per
   `AGENTS.md`'s Git Flow policy.
3. Push a `v0.2.0` tag on `master`; `.github/workflows/release.yml` then runs
   the full suite, verifies manifest versions against the tag, and publishes
   the GitHub Release.

Do not perform merge, release branch, push, or tag operations without explicit
owner approval.

## Latest local verification

Before `8f0343e`:

- `python3 -m pytest -q` -> `395 passed`
- `python3 scripts/sync_version.py --check` -> exit 0
- `python3 skills/adr-toolkit/scripts/adr.py validate --dir docs/decisions --json`
  -> 10 ADRs, no errors

After ADR-0011 creation:

- `adr.py validate --dir docs/decisions --json` -> 11 ADRs, no errors
- `adr.py index --dir docs/decisions --json` -> 11 ADRs, no warnings
- `adr.py graph --dir docs/decisions --format both --json` -> 6 rendered graph
  edges, no warnings

Run the full verification suite again before the ADR-0011 commit.

## Open risks

- `adr.py check --uncommitted` reports a `VIOLATED` finding for superseded
  ADR-0003 when changes touch `index.py`; this branch intentionally follows
  ADR-0006, which supersedes ADR-0003. Note that in PR review rather than
  treating it as a code defect.
- CHECK deliberately cannot prove prose, business rationale, or organizational
  claims; those remain human-review evidence.
- Search/relationship matching is deterministic substring/exact/prefix
  matching, untested at real scale. Revisit roadmap scale items if an adopting
  repository reaches hundreds of ADRs.
- GitHub branch/tag protection is intentionally unavailable on the current
  private plan; configure and API-verify after the repository goes public.
