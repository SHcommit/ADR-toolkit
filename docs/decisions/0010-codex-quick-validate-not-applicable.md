---
id: ADR-0010
title: Codex skill-creator's quick_validate.py incompatibility is not this project's problem
status: accepted
date: 2026-08-30
locale: en
decision_makers:
  - YangSeungHyun
related: []
affected_paths:
  - skills/adr-toolkit/SKILL.md
tags:
  - codex
  - cross-harness
  - documentation
retrospective: false
---

# Codex skill-creator's quick_validate.py incompatibility is not this project's problem

## Context and Problem Statement

Codex CLI ships a local, per-user "skill-creator" meta-skill (`~/.codex/skills/.system/skill-creator/`) with its own `quick_validate.py` lint script. That script only allows `name`, `description`, `license`, `allowed-tools`, and `metadata` in a `SKILL.md`'s frontmatter, and rejects `user-invocable` and `version` as unexpected keys. `skills/adr-toolkit/SKILL.md` carries both of those keys, because this project's own cross-harness contract and `tests/unit/test_skill_manifest.py` require them. Running that unrelated script against this repository's `SKILL.md` therefore fails.

## Decision Drivers

* Determine whether this represents a real compatibility gap this project must close, before spending effort on a fix.
* Verify the claim empirically against the actually-installed tooling rather than assuming.
* Avoid weakening this project's own cross-harness manifest contract to satisfy an unrelated tool's narrower one.

## Considered Options

* Drop `user-invocable` and `version` from `SKILL.md` to satisfy `quick_validate.py`.
* Maintain two parallel `SKILL.md` variants, one for Codex's skill-creator convention and one for the real cross-harness contract.
* Verify whether `quick_validate.py` sits on the actual plugin install/discovery path at all, and if not, take no action beyond documenting the finding.

## Decision Outcome

Chosen option: **verify, then take no action**, because `quick_validate.py` was confirmed to have no role in the actual Codex plugin install/discovery path. `codex plugin marketplace add` and `codex plugin add` (originally verified end to end for ADR-0004; re-verified in this session against Codex CLI 0.151.0, see `adapters/codex/README.md`) read only `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`; neither invokes `quick_validate.py`. That script belongs to a separate, local, per-user Codex feature for authoring brand-new, Codex-only skills from scratch with a deliberately narrower schema — it is not part of this project's distribution or install path, and this repository's `SKILL.md` was never built through that tool.

Dropping `user-invocable`/`version` to satisfy an unrelated script would break this project's actual cross-harness contract and its own tests, in exchange for satisfying a tool this project's plugin never runs through.

### Consequences

* Good: no code or contract change was needed; nothing was broken to accommodate an unrelated tool.
* Good: the reasoning is now recorded, so the question doesn't have to be re-investigated from scratch if it resurfaces (it has already been asked twice in one session).
* Bad: a user who happens to run their local `quick_validate.py` against this repository's `SKILL.md` by hand will still see a failure, with no in-repo signal explaining why — the explanation lives only in this ADR and session history, not in `SKILL.md` itself.

### Confirmation

* `codex plugin marketplace add "$(pwd)"` and `codex plugin add adr-toolkit@adr-toolkit-marketplace` were re-run against Codex CLI 0.151.0 in an isolated `CODEX_HOME`; both succeeded and read `.claude-plugin/plugin.json`, never `quick_validate.py`.
* `python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/adr-toolkit` was run directly and reproduced the reported failure, confirming the claim while also confirming it sits outside the install path.

## Pros and Cons of the Options

### Drop the two keys from SKILL.md

* Good, because it would satisfy `quick_validate.py`.
* Bad, because it breaks this project's own cross-harness contract and `test_skill_manifest.py` for a tool that never actually reads this file during real plugin installation.

### Maintain two SKILL.md variants

* Good, because both conventions could theoretically be satisfied at once.
* Bad, because it reintroduces exactly the drift risk this project has repeatedly hardened against (see ADR-0004's single-canonical-package rationale), for a tool with no install-path role.

### Verify, then take no action

* Good, because it costs nothing and is backed by an actual reproduction against the real tooling, not assumption.
* Bad, because the explanation is not discoverable from `SKILL.md` itself if the question resurfaces outside this session.

## Revisit Triggers

* Codex's actual plugin install/discovery path changes to route through `quick_validate.py` or an equivalent check, making this a real compatibility gap.
* A future Agent Plugins spec revision standardizes `user-invocable`/`version`-equivalent keys in a way `quick_validate.py`'s allowed set would need updating for anyway.
