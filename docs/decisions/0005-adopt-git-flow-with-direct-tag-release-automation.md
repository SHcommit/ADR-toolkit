---
id: ADR-0005
title: Adopt Git Flow with direct-tag release automation
status: accepted
date: 2026-08-30
decision_makers:
  - YangSeungHyun
locale: en
related: []
affected_paths:
  - AGENTS.md
  - .github/workflows/
  - skills/adr-toolkit/VERSION
  - scripts/sync_version.py
tags:
  - process
  - release
  - git-flow
retrospective: false
---

# Adopt Git Flow with direct-tag release automation

## Context and Problem Statement

The 4-plan MVP was built entirely on one long-lived feature branch with no branch policy; `master` held only the initial commit throughout. Now that the MVP is complete and released as v0.1.0, the project needs an explicit branch and release policy for future work, including how a version gets tagged and published.

## Decision Drivers

* A predictable integration point for future feature/fix/docs work
* Low operational overhead appropriate for a solo/small-team repository
* Reuse the release automation already built and verified in Plan 4, rather than replacing it speculatively

## Considered Options

* Git Flow (`develop`/`master`/`feature`/`release`/`hotfix` branches) with direct-tag release automation
* Git Flow with release-pr automation (Release Please, auto-generating release PRs from Conventional Commits)
* Trunk-based development (small changes merged frequently, feature flags for incomplete work)
* GitHub Flow (one production branch, short-lived feature branches, continuous deployment)

## Decision Outcome

Chosen option: **Git Flow with direct-tag release automation**, because the project already has more than one long-lived integration point in practice (this MVP's own multi-plan history, and future feature batches), and an explicit `develop`/`master` split matches that; direct-tag was chosen over release-pr because Plan 4 already built, task-reviewed, and whole-branch-reviewed a working tag-triggered `release.yml` — replacing tested automation with an unverified new mechanism for a solo/small-team repo trades working automation for unverified automation with no clear benefit yet.

### Consequences

* Good: reuses release automation that is already tested and was independently re-verified during its own final review; explicit branch roles reduce ambiguity for future contributors.
* Bad: Git Flow's extra branch layer (`develop` plus `release/*`) is more ceremony than Trunk-based or GitHub Flow would need for a project this size; direct-tag requires a human to remember to bump `VERSION` and tag correctly, rather than deriving a version automatically from commit history.

### Confirmation

`AGENTS.md`'s "Git Flow Branch and Release Policy" section states the policy in full; `.github/workflows/release.yml` triggers only on `v*` tag pushes and never auto-bumps a version.

## Pros and Cons of the Options

### Git Flow with direct-tag release automation

* Good, because it reuses release automation already built, tested, and verified in this repository
* Bad, because a human must remember every version bump and tag correctly; nothing derives the version from commit history

### Git Flow with release-pr automation

* Good, because changelog and version bumps are generated automatically from Conventional Commit history, reducing human error
* Bad, because it requires disciplined Conventional Commit usage across all contributors and replaces working, verified automation with an unverified new mechanism

### Trunk-based development

* Good, because it minimizes branch ceremony and integration lag for a small, fast-moving codebase
* Bad, because it assumes continuous feature-flag discipline this project has not adopted, and offers no natural checkpoint for a deliberate, reviewed release like v0.1.0

### GitHub Flow

* Good, because it is simpler than Git Flow with only one long-lived branch to reason about
* Bad, because it has no dedicated integration branch separate from production, which matters once multiple features are in flight at once — a scenario this project has already lived through with its 4-plan MVP

## Revisit Triggers

* The team grows beyond solo/small-team and reliable Conventional Commit discipline becomes realistic — revisit toward release-pr automation.
* `develop` and `release/*` prove to be pure overhead with no multi-stream benefit in practice — revisit toward GitHub Flow.
