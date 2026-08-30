---
id: ADR-0004
title: Adapter packaging: manifest-only directories, install-time symlinks, verified formats
status: accepted
date: 2026-08-30
decision_makers: []
related: []
affected_paths:
  - adapters/
tags:
  - adapters
  - harness-support
retrospective: false
---

# Adapter packaging: manifest-only directories, install-time symlinks, verified formats

## Context and Problem Statement

The toolkit ships as one self-contained `skills/adr-toolkit/` package usable by multiple harnesses (Claude Code, Codex CLI, Gemini CLI, Antigravity CLI). Every harness format actually investigated expects a sibling `skills/` directory next to its own manifest file, but duplicating the package once per harness would violate the single-source-of-truth goal that motivated the self-contained package in the first place. Separately, the exact manifest fields for three of the four harnesses were never verified against real documentation before Plan 4 — and guessing already produced a real bug once (Plan 1's Claude Code adapter guessed a `"skills"` key and a nested manifest path that turned out wrong, caught only by that plan's final review).

## Considered Options

* Copy the full `skills/adr-toolkit/` package into each `adapters/<harness>/` directory
* Symlink `skills/adr-toolkit/` into each adapter directory and commit the symlink to git
* Document the symlink as a manual install-time step (never committed), and verify each harness's real manifest format against its actual documentation before writing it

## Decision Outcome

Chosen option: **document the symlink as an install-time step, with formats verified not guessed**, because copying reintroduces drift between copies, committing a symlink breaks on a Windows checkout without `core.symlinks` enabled (this repo's own CI matrix includes `windows-latest`), and guessing manifest formats already produced two real bugs (Claude Code in Plan 1, Codex CLI in Plan 4) that only an actual install-and-run caught.

## Consequences

* Good: one canonical copy of the skill package exists; no manifest format ships without being checked against real documentation or a real install attempt where a harness CLI was available.
* Bad: a user must run one extra manual `ln -s` step before an adapter works — installation cannot be a true zero-step "clone and go."

## Confirmation

`git ls-tree` on any `adapters/<harness>/` directory shows no `120000` (symlink) mode entries; every adapter's `README.md` documents the symlink as an install step; `.gitignore` ignores each adapter's `skills/` path.

## Revisit Triggers

* A harness's real plugin format later supports referencing an external path directly, removing the need for that harness's symlink step — revisit that harness's adapter specifically, not this policy as a whole.
