---
id: ADR-0007
title: Promote CHECK's kind-to-confidence mapping to a stable output field
status: accepted
date: 2026-08-30
locale: en
decision_makers:
  - YangSeungHyun
related: []
affected_paths:
  - skills/adr-toolkit/scripts/commands/check.py
  - README.md
  - skills/adr-toolkit/SKILL.md
  - skills/adr-toolkit/references/conflict-rules.md
  - examples/quickstart.md
  - tests/unit/test_check.py
tags:
  - check
  - confidence
  - v0.2.0
retrospective: false
---

# Promote CHECK's kind-to-confidence mapping to a stable output field

## Context and Problem Statement

CHECK findings carried an ad-hoc `kind` value (`verified_violation`, `review_required`, `related`, `no_applicable_constraint`). README, SKILL.md, and `references/conflict-rules.md` already documented a mapping from each `kind` to a governance confidence meaning (`VERIFIED`, `VIOLATED`, `UNVERIFIABLE`, `NOT_APPLICABLE`), but that mapping existed only in prose. Every agent consuming CHECK output had to re-derive it from documentation on every run instead of reading it off the result.

## Decision Drivers

* Give CHECK a stable, machine-readable confidence contract instead of leaving classification to prose the agent must re-read every time.
* Avoid breaking existing consumers and tests that already assert on `kind`.
* Keep the change additive and low-risk given the size of the existing CHECK test suite.

## Considered Options

* Leave the mapping in documentation only; require agents to re-derive it each run.
* Replace `kind` entirely with the four-value `confidence` vocabulary.
* Add `confidence` as a new field computed from the existing `kind`, leaving `kind` unchanged.

## Decision Outcome

Chosen option: **add `confidence` as a new field computed from `kind`**, because it makes the already-documented contract machine-readable without touching `kind`'s sixteen existing test assertions or any consumer that already keys off it.

Every finding of `kind: verified_violation` now also carries `confidence: VIOLATED`; `related` carries `VERIFIED`; `review_required` and `no_applicable_constraint` both carry `UNVERIFIABLE`. An empty `findings` list still means `NOT_APPLICABLE` — that value has no corresponding per-finding `kind`, since no finding is emitted when no ADR governs the changed paths at all.

### Consequences

* Good: agents (and any other consumer) read `confidence` directly instead of re-deriving it from prose on every run.
* Good: `kind` and every existing test assertion on it are untouched — zero regression risk to the CHECK test suite.
* Bad: two overlapping fields (`kind` and `confidence`) now exist on every finding; a future cleanup could consider whether `kind` should eventually be retired once all consumers move to `confidence`.

### Confirmation

* `tests/unit/test_check.py` asserts the exact `confidence` value for each of the four `kind` values, including the superseded-reference violation path.
* `python3 -m pytest -q` passes (327 tests) after the change.
* README's "CHECK confidence" table, SKILL.md's CLASSIFY step, and `references/conflict-rules.md`'s evidence-confidence table were updated to describe the field instead of a derivation the agent had to perform.

## Pros and Cons of the Options

### Leave the mapping in documentation only

* Good, because it requires no code change.
* Bad, because every agent run re-derives the same fixed mapping from prose, which is exactly the kind of repeatable, low-judgment work a deterministic core should own.

### Replace `kind` with `confidence` entirely

* Good, because it removes the two-field redundancy.
* Bad, because it breaks sixteen existing test assertions and any external consumer already keyed off `kind`, for no functional gain over the additive approach.

### Add `confidence` as a new field

* Good, because it is purely additive: no existing behavior, test, or consumer changes.
* Bad, because the two fields overlap in meaning, which a future major version could choose to collapse.

## Revisit Triggers

* A future breaking release consolidates `kind` and `confidence` into a single field once external consumers no longer depend on `kind` alone.
* A fifth finding shape is added that doesn't map cleanly onto the four confidence values, requiring the mapping itself to be revisited.
