---
id: ADR-0017
title: Adopt source-controlled GitHub governance and CI supply-chain hardening
status: accepted
date: 2026-09-06
locale: en
decision_makers:
  - YangSeungHyun
related:
  - ADR-0005
  - ADR-0016
affected_paths:
  - .github/CODEOWNERS
  - .github/dependabot.yml
  - .github/labeler.yml
  - .github/labels.yml
  - .github/ISSUE_TEMPLATE/
  - .github/workflows/test.yml
  - .github/workflows/release.yml
  - pyproject.toml
  - scripts/export_dev_requirements.py
  - tests/unit/test_github_governance.py
  - SECURITY.md
tags:
  - github
  - governance
  - supply-chain
  - ci
  - security
retrospective: false
---

# Adopt source-controlled GitHub governance and CI supply-chain hardening

## Context and Problem Statement

The repository became public on 2026-08-29 and shipped v1.0.0/v1.0.1, but the
day-to-day contributor mechanics that keep a growing issue/PR queue navigable
for a single maintainer were never built out. Labels were the GitHub defaults,
issue templates were legacy Markdown, and there was no Dependabot, no
CODEOWNERS, no path-based auto-labeler, no lint job, and no dependency/security
scan. A prior audit also queried only the classic branch-protection endpoint
and wrongly concluded the repo was unprotected; the repository ruleset API
showed active branch/tag rulesets since 2026-09-02, but their required
status-check names can drift whenever the CI matrix changes.

## Decision Drivers

* One maintainer and one repository: automation must pay for itself without
  assuming a team that does not exist yet.
* CI was already mature (multi-OS pytest matrix, coverage floor, scoped mypy
  --strict, drift gates, pr-title-check, harness-parity) but had no lint and no
  dependency/security scan.
* harness-parity ran a remote `curl | bash` installer -- a supply-chain risk.
* Every "not now" item must carry a written trigger, not a vague "later".

## Considered Options

* Keep hand-triage only -- does not scale past a handful of issues.
* Adopt GitHub-native automation as code (labels, labeler, Dependabot, Issue
  Forms) plus lint + dependency-audit CI gates, and sync the ruleset's required
  checks to the CI matrix -- chosen.
* Add heavy automation now (mandatory CODEOWNERS review, stale bot, org-wide
  rulesets) -- deferred behind explicit preconditions.

## Decision Outcome

Chosen option: **source-controlled GitHub governance + CI supply-chain
hardening**, because it lets issues/PRs self-organize and keeps required checks
honest without over-automating a one-maintainer repository.

* Path-based auto-labeler mapping changed-file globs to `area:*` labels, plus a
  source-controlled label taxonomy (`.github/labels.yml`) synced live without
  deleting unrelated labels.
* Dependabot for pip and github-actions only, weekly, grouped, targeting
  `develop`.
* Structured Issue Forms for bug and feature reports, with `config.yml` routing
  questions to Discussions and vulnerabilities to `SECURITY.md`.
* Fast CI gates: ruff lint and `pip-audit --strict`; the Python floor moved from
  3.9 to 3.10.
* Supply-chain hardening: the Antigravity `curl | bash` installer was replaced
  with a versioned SHA-512-verified artifact; release Actions were pinned to
  commit SHAs; the PR-title shell expression injection was removed.
* Branch ruleset `22101891` required checks were synced to the new matrix
  (Python 3.10 x3 + `lint` + `dependency-audit` added; Python 3.9 removed) and
  re-verified through the effective-rules API.
* A dormant CODEOWNERS was drafted but not wired to required review. Live
  Discussions, Dependabot security updates/alerts, secret scanning + push
  protection, and private vulnerability reporting were enabled.

## Consequences

* Good: new issues/PRs arrive pre-labeled; dependency bumps arrive as routine,
  reviewable PRs; CI fails fast on lint and known vulnerabilities; protected
  branches can no longer be silently blocked by a stale required-check name.
* Bad: ruleset required checks are GitHub-side settings that cannot live fully
  in code, so a future CI job rename still requires a manual ruleset sync; the
  trigger for a read-only verification script is recorded in `improvements.md`.

## Confirmation

pytest (562 passed) plus branch coverage, ruff check, scoped mypy --strict,
`sync_version.py --check`, and `verify_examples.py --check` all passed. The
ruleset and effective-rules APIs confirm the new required checks are active for
`develop`.

## Revisit Triggers

* A second qualified maintainer appears -> enable CODEOWNERS required review.
* A second repository repeats the same operations -> org-level rulesets,
  reusable workflows, audit export, and taxonomy.
* A real abandoned-issue backlog accumulates -> stale bot.
* CI check-name drift recurs -> ruleset-as-code or a read-only verification
  script.
