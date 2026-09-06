# OSS Repository Governance & Hardening Design

## Scope

Make ADR Toolkit's GitHub operations (issue/PR triage, labels, dependency
updates, CI gates, branch protection, contributor onboarding) hold up if
issues and PRs grow from single digits into the hundreds, without adding
automation the current one-maintainer, one-repository reality doesn't need
yet. Covers `.github/**` configuration, CI workflow structure, and the
GitHub-side settings that can't live in code. Does not change ADR Toolkit's
product code, CLI behavior, or `docs/decisions/` governance model.

## Context — audit findings as of 2026-09-05

> **2026-09-06 review correction:** the original audit queried only the
> classic branch-protection endpoint. A 404 from that endpoint does not prove
> repository rulesets are absent. Ruleset and effective-rules APIs show that
> active branch/tag rulesets have existed since 2026-09-02 (IDs `22101891`
> and `22102322`). The original audit also incorrectly described the
> Antigravity adapter as manual-only even though `harness-parity` executed its
> remote bootstrapper. The decisions below are corrected accordingly.

Re-verified against the live repository (`gh api`/`gh repo view`), not just
file presence, because `docs/enterprise-adoption.md` §4/§8 described this repo
as still private with a single precondition ("저장소 public 전환") blocking the
public-readiness gate. That precondition had already been met and the document
was stale:

- The repository has been **public since 2026-08-29**, and `master` has
  already shipped `v1.0.0` and `v1.0.1` (PyPI publishing pipeline, antigravity
  harness-parity CI, a Windows lock-metadata fix, mypy `--strict` fix).
- Active repository rulesets protect `master`, `develop`, `release/*`, and
  `v*` tags. They require PRs, status checks, conversation resolution, and
  prohibit deletion/non-fast-forward updates without a bypass actor. The
  remaining rollout concern is keeping required-check contexts synchronized
  with CI matrix changes (this branch replaces Python 3.9 with 3.10).
- `develop` was frozen at the `v0.3.2` sync point while `master` advanced
  through the `v1.0.0`/`v1.0.1` releases — the git-flow-mandated
  release-branch back-merge into `develop` never happened. **Fixed as a
  prerequisite to this spec** via `chore/sync-develop-with-v1.0.1` (PR #17,
  not yet merged at spec time) — this branch is based on that synced state.
- No `dependabot.yml`, no `CODEOWNERS`, no path-based auto-labeler. Labels are
  the unmodified GitHub defaults (`bug`, `enhancement`, `documentation`,
  `good first issue`, `help wanted`, `question`, `duplicate`, `invalid`,
  `wontfix`, `accessibility`) — no `type:`/`area:`/`priority:`/`size:` axis at
  all, so nothing about a large backlog would currently self-organize.
  Issue templates are legacy Markdown (`bug_report.md`, `feature_request.md`),
  not structured Issue Forms.
- CI (`.github/workflows/test.yml`) is already more mature than a typical
  small OSS repo: multi-OS/multi-Python pytest matrix, a coverage floor
  (`--cov-fail-under=85`), a scoped mypy `--strict` job, generated-file drift
  checks (`sync_version.py --check`, `verify_examples.py --check`), a
  Conventional-Commit PR title gate, and a `harness-parity` job that installs
  the real Codex/Gemini CLIs against this repo. There is **no lint job** at
  all (no ruff/flake8/black anywhere in the repo) and no dependency/security
  scan step.
- `harness-parity` contains one remote-installer pattern the request asked to
  scrutinize: `curl -fsSL https://antigravity.google/cli/install.sh | bash`.
  This does run in CI before the Antigravity end-to-end adapter verification,
  so it must be replaced with a versioned artifact plus checksum verification.
- GitHub Actions are pinned to major-version tags from verified publishers
  (`actions/*@v4/@v5`, `softprops/action-gh-release@v2`,
  `pypa/gh-action-pypi-publish@release/v1`) — not full commit-SHA pinning, but
  not `@latest`/`@master` either. `release.yml` already scopes permissions
  per-job (`contents: write`, `id-token: write`, `attestations: write`) and
  `test.yml` sets repo-wide `permissions: contents: read`; least-privilege is
  already largely in place, not a gap.
- Dependency ecosystems actually in use: Python (`pyproject.toml`) and GitHub
  Actions. The only `package.json` is a test fixture; the `npm install -g`
  calls in `harness-parity` install pinned global CLIs for testing, not a
  project dependency Dependabot should manage. No Docker.
- `project-roadmap.md`'s "Public and enterprise governance" section and
  `docs/enterprise-adoption.md` §8 already correctly defer **mandatory**
  CODEOWNERS review and organization-wide ruleset/reusable-workflow work
  behind explicit preconditions (2+ qualified maintainers; 2+ repositories)
  that still aren't met. This spec does not revisit that call — see
  Out of Scope.

## Problem Statement

The repository's day-to-day contributor mechanics (label triage and dependency
freshness) were never built out because the
project was small and private. It is now public with two releases shipped,
but the operational scaffolding that keeps a growing issue/PR queue navigable
for a single maintainer does not exist yet. Existing rulesets protect release
history, but their required status-check names can drift when CI changes.
Left as-is, the first sign of trouble will be either a permanently blocked PR
after a matrix rename, or a backlog of unlabeled, untriaged work.

## Solution

Add the minimum GitHub-native automation that lets issues and PRs
self-organize (path-based labels, a label taxonomy, Dependabot, Issue Forms)
and verify/update the already-active rulesets alongside CI changes,
while explicitly deferring anything that assumes a maintainer team or an
issue volume this repository doesn't have yet (mandatory CODEOWNERS review,
stale-bot, org-wide rulesets). Every "not now" gets a written trigger
condition instead of a vague "later," matching how `project-roadmap.md` and
`docs/enterprise-adoption.md` already record deferred work in this repo.

## User Stories

1. As the sole maintainer, I want new issues/PRs to arrive pre-labeled by the
   file paths they touch so I don't manually triage every one.
2. As the sole maintainer, I want dependency and Action version bumps to
   arrive as routine, reviewable PRs instead of silent drift or a manual audit.
3. As a first-time contributor, I want a structured bug/feature form instead
   of a blank Markdown template, so I give the maintainer what's needed on
   the first pass.
4. As the sole maintainer, I want `master`/`develop`/`v*` protection verified
   through the correct ruleset APIs and required checks kept in sync, without
   mandatory independent code-owner review I can't actually staff.
5. As a future contributor, I want a small set of well-labeled "good first
   issue" candidates to exist so I know where to start.
6. As the sole maintainer, I want CI to catch missing lint/security-scan
   coverage that today has no job at all, without turning every PR into a
   slow, heavyweight gate.

## Decisions

### NOW — apply in this branch

- **Path-based auto-labeler**: a labeler config mapping changed-file globs to
  `area:*` labels (e.g. `skills/adr-toolkit/**` / `scripts/**` → `area:core`,
  `adapters/**` → `area:adapter`, `.github/**` → `area:github`, `docs/**` →
  `area:docs`, `tests/**` → `type:test`), run by a workflow triggered on
  `pull_request_target` with `contents: read`/`pull-requests: write` only.
- **Label taxonomy**: introduce `type:*`, `area:*`, `priority:*`, `size:*`,
  plus `needs-triage` and `blocked`, sized to this repo's actual directories
  (`core`/`cli`/`adapter`/`github`/`docs`) rather than the generic list
  verbatim. Keep the existing default labels (`bug`, `enhancement`,
  `good first issue`, `help wanted`, `documentation`) rather than replacing
  them, since GitHub's defaults already cover part of `type:*`/`area:docs`
  and dropping them would break any existing issue/PR history referencing
  them.
- **Dependabot**: `pip` (root `pyproject.toml`) and `github-actions`
  ecosystems only — no `npm`/`docker` entries, since neither has a manifest
  Dependabot could act on. Weekly schedule, grouped updates, auto-created
  PRs.
- **Issue Forms**: replace the two Markdown templates with structured YAML
  forms (bug report: version, OS, environment, affected
  component/adapter, expected/actual behavior, repro steps, logs; feature
  request: problem, use case, proposed solution, alternatives, affected
  area, contribution willingness), plus a `config.yml` pointing to
  Discussions/`SECURITY.md` for questions and vulnerabilities instead of a
  blank issue.
- **Lint CI job**: add a fast lint job (the repo has no lint tool configured
  at all today) to the existing fast-gate jobs in `test.yml`, separate from
  the slower `harness-parity` job.
- **Dependency/security scan**: add a lightweight `pip-audit`-style check for
  the Python dependency surface as a fast-gate job.
- **Branch protection / ruleset** (GitHub UI/API, not a file in this repo —
  see the UI section below): verify the existing active rulesets, then update
  required status-check contexts after CI job/matrix changes. They already
  require PR + passing checks, block force-push/deletion on protected branches
  and `v*`, and require conversation resolution. Do **not**
  require code-owner review or signed commits yet — no second qualified
  maintainer exists to review against, and no CODEOWNERS file exists to
  reference.
- **Update stale docs**: correct `docs/enterprise-adoption.md` §4/§8's
  "저장소가 아직 private" framing and `improvements.md`'s already-removed
  precondition note now that the public transition and its ruleset gate are
  being closed out, so the next reader doesn't re-derive the same stale
  premise this session had to correct first.

### NEXT — once issue/PR volume or contributor count actually grows

- CODEOWNERS file (drafted but **not** wired to mandatory review) — ready to
  flip on once 2+ qualified maintainers exist, per the existing decision in
  `docs/enterprise-adoption.md` §4 and `project-roadmap.md`. Do not enable
  required review as part of this spec.
- GitHub Projects board with an Inbox → Backlog → Ready → In Progress →
  Review → Blocked → Done flow and `Priority`/`Area`/`Size` custom fields,
  once there's enough issue volume for a Kanban view to earn its keep over a
  flat issue list.
- PR size labeling (`size:XS`…`size:XL`) as a workflow addition once PR
  volume makes "the queue is large, which PRs are actually small" a real
  question.
- Splitting `test.yml` into an explicit Fast Gate / Integration Gate
  workflow pair, once the existing single-workflow job list gets unwieldy
  enough that PR authors need the distinction visible rather than just
  reading job names.

### LATER — only once scale actually demands it

- Stale issue/PR bot. Current issue/PR count doesn't warrant it — explicit
  decision **not to adopt now**, matching how this repo already declines
  automation it doesn't need (`docs/enterprise-adoption.md` §8 "지금 구현하지
  않을 것"). Revisit once there's a real backlog of abandoned issues, with
  exclusions for `security`, `pinned`, `roadmap`, `help wanted`,
  `priority:P0`, and `blocked`.
- Organization-level rulesets, reusable workflows, RBAC, audit export — all
  already correctly gated behind "2+ repositories" in `improvements.md`;
  this spec doesn't touch that precondition.
- Advanced/ML-based triage bots, automatic contributor assignment, complex
  multi-stage release trains.

## Testing / Validation Decisions

- Labeler config: validate with a dry-run against recent merged PRs'
  changed-file lists to confirm expected labels before enabling the workflow
  for real.
- Dependabot: confirm via a manual `dependabot.yml` schema check (GitHub
  validates on push) and by watching the first scheduled run produce the
  expected grouped PRs.
- Issue Forms: manually preview each form in GitHub's issue-form preview
  before merging; forms have no automated test surface.
- New CI jobs (lint, dependency/security scan): must pass on this branch's
  own diff and not regress the existing 515 unit tests or `sync_version.py
  --check` / `verify_examples.py --check` drift gates.
- Branch protection: query `repos/SHcommit/ADR-toolkit/rulesets/<id>` and
  `repos/SHcommit/ADR-toolkit/rules/branches/<branch>`. Do not use the classic
  `branches/<branch>/protection` endpoint alone as evidence of ruleset absence.

## Out of Scope

- Mandatory CODEOWNERS-backed independent review (no second qualified
  maintainer yet — explicit existing decision, not revisited here).
- Organization-level rulesets, reusable workflows, audit export, central
  taxonomy (single-repository precondition unmet — explicit existing
  decision, not revisited here).
- Stale-bot / auto-triage-bot / auto-assignment automation (volume doesn't
  warrant it yet).
- Signed-commit requirements.
- Any change to ADR Toolkit's product code, CLI, or `docs/decisions/`
  governance model.
- Full commit-SHA pinning for all third-party Actions (current major-version
  tag pinning from verified publishers is a reasonable middle ground for this
  repo's risk level; revisit only if a specific tag-mutation incident in one
  of the pinned Actions ever demonstrates the gap matters).

## Open Questions

- Should PR #17 (the develop/master sync) merge before or independently of
  this branch's PR? This branch is based on its tip either way, so either
  order is safe, but the maintainer should decide merge order.
- Exact `priority:*` and `size:*` thresholds (e.g. what LOC/file-count counts
  as `size:M` vs `size:L`) — left to the maintainer's judgment at
  implementation time rather than guessed here.
- Whether `needs-triage` should auto-apply to every new issue/PR via the
  labeler workflow, or only to issues (PRs already get `area:*` +
  `pr-title-check`) — implementation-time call.

## Further Notes

- Rollout order: ruleset verification/check-context sync (GitHub UI/API) →
  Dependabot + auto-labeler (lowest
  maintenance cost) → Issue Forms → new CI jobs (lint, dependency scan) →
  stale-docs correction, so the highest-value, lowest-risk items land first
  and the doc correction reflects the final state rather than needing a
  second pass.
- The headline review correction is methodological: classic branch protection
  and repository rulesets use different APIs. Operational audits must inspect
  both, then query effective rules for concrete refs before declaring a gap.
- This spec intentionally does not propose a `.github/labeler.yml` /
  `dependabot.yml` schema inline — implementation will write those files
  directly against this repo's actual directory names, which is faster to
  verify than hand-transcribing YAML into a design doc that could drift from
  the real paths by the time it's implemented.
