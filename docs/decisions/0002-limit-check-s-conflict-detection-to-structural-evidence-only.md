---
id: ADR-0002
title: Limit CHECK's conflict detection to structural evidence only
status: accepted
date: 2026-08-30
decision_makers:
  - YangSeungHyun
locale: en
related: []
affected_paths:
  - skills/adr-toolkit/scripts/commands/check.py
  - skills/adr-toolkit/scripts/commands/diff.py
  - skills/adr-toolkit/scripts/core/constraints.py
  - skills/adr-toolkit/scripts/rules/conflict.py
  - skills/adr-toolkit/references/conflict-rules.md
tags:
  - check
  - mvp-scope
  - architecture
retrospective: true
---

# Limit CHECK's conflict detection to structural evidence only

## Context and Problem Statement

CHECK needs to flag conflicts between a diff and existing Accepted ADRs. The original PRD's 8-type conflict taxonomy includes types (Direct violation via SDK-call detection, Pattern divergence) that require semantic understanding of code intent, which cannot be reliably detected without deep static analysis (AST or import-graph tooling). Shipping unverified semantic detection in a brand-new tool's MVP risks false positives on day one, which is the fastest way to lose adopter trust.

## Considered Options

* Full semantic/AST-based conflict detection matching the original 8-type taxonomy
* Structural-evidence-only detection via a fixed `constraints:` YAML rule vocabulary (`forbidden_import`, `required_path`, `forbidden_path`, `dependency_forbidden`, `file_must_exist`, `test_must_exist`)

## Decision Outcome

Chosen option: **structural-evidence-only detection**, because false positives are the fastest way to lose trust in a brand-new open-source tool, and a fixed rule vocabulary keeps CHECK's core deterministic, matching the project's own Deterministic Core / Agentic Edge principle.

## Consequences

* Good: CHECK never has to make an ambiguous semantic judgment call; every finding is traceable to an explicit, author-written rule.
* Bad: CHECK cannot catch a conflict that requires understanding code intent unless an explicit structural rule was already written for it — semantic drift can slip through undetected.

## Confirmation

`skills/adr-toolkit/scripts/rules/conflict.py` implements exactly four structural matching mechanisms and nothing else; no test in `tests/unit/test_conflict.py` attempts semantic or AST-based matching.

## Confirmed Evidence

The repository implements a fixed six-kind constraint vocabulary in
`core/constraints.py`, evaluates it through structural path and line matching
in `rules/conflict.py`, and collects Git diff evidence in `commands/diff.py`.
The unit and integration suites exercise those deterministic boundaries. This
ADR was written retrospectively from that implemented MVP state.

## Inferred Rationale

The trust argument in this record is a reconstruction from the implemented
scope and design material: limiting CHECK to rules it can prove appears to have
been preferred over heuristic semantic coverage because false confidence would
be more damaging than an explicit `UNVERIFIABLE` result.

## Unknown

The exact contemporaneous discussion, relative weighting of the alternatives,
and any rejected semantic-analysis prototypes were not preserved.

## Revisit Triggers

* Real usage produces enough false-negative reports that users want semantic detection — tracked as "Full semantic conflict taxonomy" in `project-roadmap.md`.
