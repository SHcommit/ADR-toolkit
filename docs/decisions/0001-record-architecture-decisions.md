---
id: ADR-0001
title: Record architecture decisions
status: accepted
date: 2026-08-30
decision_makers:
  - YangSeungHyun
locale: en
related: []
affected_paths:
  - docs/decisions/
tags:
  - process
retrospective: false
---

# Record architecture decisions

## Context and Problem Statement

We need a consistent way to capture and communicate significant
architectural decisions so future contributors (human or agent) can find
the reasoning behind them.

## Considered Options

* No formal record, rely on commit messages and memory
* Wiki or external documentation tool
* Architecture Decision Records stored alongside the code

## Decision Outcome

Chosen option: **Architecture Decision Records stored alongside the code**, because they version with the code, stay close to what they describe, and are readable by both humans and coding agents.

## Consequences

* Good: decisions and their rationale are discoverable in the repository itself.
* Bad: requires discipline to keep records up to date as decisions evolve.

## Confirmation

`python3 skills/adr-toolkit/scripts/adr.py validate --dir docs/decisions --json`
validates the records, and `index` regenerates `docs/decisions/README.md` from
the same directory.

## Revisit Triggers

* The team adopts a different documentation system project-wide.
