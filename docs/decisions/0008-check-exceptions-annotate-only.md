---
id: ADR-0008
title: Deterministic CHECK policy exceptions: schema-validated, annotate-only, never suppress
status: accepted
date: 2026-08-30
locale: en
decision_makers:
  - YangSeungHyun
related: []
affected_paths:
  - skills/adr-toolkit/scripts/core/exceptions.py
  - skills/adr-toolkit/scripts/commands/exception.py
  - skills/adr-toolkit/scripts/commands/check.py
  - skills/adr-toolkit/scripts/adr.py
  - skills/adr-toolkit/schemas/exception.schema.json
  - README.md
  - skills/adr-toolkit/SKILL.md
  - skills/adr-toolkit/references/conflict-rules.md
tags:
  - check
  - exceptions
  - governance
  - v0.2.0
retrospective: false
---

# Deterministic CHECK policy exceptions: schema-validated, annotate-only, never suppress

## Context and Problem Statement

`register_exception` has always been one of CHECK's five documented resolutions for a Verified violation, but it existed only as a string label. There was no schema for what an exception must record, nowhere to store one, and no way for a later CHECK run to recognize that a specific violation had already been reviewed and accepted. Anyone who picked `register_exception` had no deterministic next step.

## Decision Drivers

* Give `register_exception` a real, followable path instead of a dead-end label.
* Never let CHECK present a false "clean" result — this project's core principle is that a clean result must never be confused with proof of compliance.
* Keep exceptions scoped, owned, and time-boxed rather than a blanket, permanent rule bypass.
* Reuse the existing deterministic-core patterns (schema validation, sequential IDs, one JSON record per exception) instead of inventing a new mechanism.

## Considered Options

* Leave `register_exception` as a label only, with no backing schema or storage.
* Build a full exception system where a matching, active exception suppresses the violation from future CHECK runs.
* Build a schema-validated exception record (`owner`, `reason`, `scope`, `expiry`, `adr_id`, `rule_id`) that CHECK annotates onto a matching finding, but never uses to hide or downgrade it.

## Decision Outcome

Chosen option: **schema-validated exception records that CHECK annotates but never suppresses**, because any mechanism that makes an accepted violation silently disappear from CHECK's output would directly contradict this project's "no false governance confidence" principle — a human scanning CHECK results must still see every structurally confirmed violation, exception or not.

`adr.py exception --input <file.json>` validates a draft against `schemas/exception.schema.json` (`owner`, `reason`, `scope`, `expiry`, `adr_id`, `rule_id` all required; `scope` must be a non-empty list of path patterns narrower than the rule itself) and writes `docs/decisions/exceptions/EXC-NNNN.json`. CHECK loads every active (schema-valid, non-expired) exception on each run and, for a `verified_violation` finding whose `adr_id`, `rule_id`, and file path all match, attaches an `exception` field carrying the exception's id, owner, reason, and expiry. The finding's `kind` and `confidence` stay exactly what the structural evidence says. A malformed exception file degrades to a `BAD_EXCEPTION` warning rather than aborting the run, matching the existing ADR/constraints degradation pattern.

### Consequences

* Good: `register_exception` is now a real, deterministic, auditable action instead of a dead-end label.
* Good: an exception can never cause CHECK to under-report a real violation — the worst case is a violation the reader already expects to see, now with context attached.
* Good: `scope` forces an exception to be narrower than the rule it excepts, and `expiry` forces it to be time-boxed rather than a permanent bypass.
* Bad: a violation with an active exception still appears in every CHECK run, which is by design but means CHECK output stays "noisy" for accepted, reviewed exceptions rather than going quiet.
* Bad: exceptions are matched by exact `adr_id`/`rule_id`/scoped-path equality only — no notion of exception review, renewal workflow, or expiry notification exists yet.

### Confirmation

* `tests/unit/test_exceptions.py` covers schema validation, expiry, and scope matching.
* `tests/unit/test_exception_command.py` covers the `exception` command's id assignment, dry-run, and error paths.
* `tests/unit/test_check.py` covers a matching active exception being annotated, an expired exception not applying, an out-of-scope exception not applying, and a malformed exception file degrading to a warning.
* The documented `adr.py exception` command was run end to end in a scratch repository and produced the exact output shown in the README.

## Pros and Cons of the Options

### Leave `register_exception` as a label only

* Good, because it requires no new code, schema, or storage format.
* Bad, because it leaves one of CHECK's five documented resolutions with no actual mechanism behind it.

### Suppress matching violations from future CHECK runs

* Good, because accepted exceptions would stop generating repeat noise on every run.
* Bad, because it lets CHECK present a "clean" result over a structurally confirmed violation, which this project's own principles explicitly reject as false governance confidence.

### Schema-validated, annotate-only exceptions

* Good, because it makes `register_exception` real and auditable while keeping every violation visible.
* Bad, because CHECK output never goes fully quiet for a repository carrying accepted exceptions — a deliberate tradeoff, not an oversight.

## Revisit Triggers

* Real usage shows accepted-exception noise is a genuine workflow problem, motivating a filtered or grouped view rather than suppression itself.
* Multiple exceptions accumulate to the point that an `adr.py exception list` or expiry-reporting command becomes worth building.
* Organizations need exception approval workflows (multi-party sign-off) beyond a single `owner` field.
