---
id: ADR-0004
title: Adapter packaging: manifest-only directories, install-time symlinks, verified formats
status: accepted
date: 2026-08-30
decision_makers:
  - YangSeungHyun
locale: en
related: []
affected_paths:
  - adapters/
  - .gitignore
  - .claude-plugin/marketplace.json
  - .claude-plugin/plugin.json
tags:
  - adapters
  - harness-support
retrospective: true
---

# Adapter packaging: manifest-only directories, install-time symlinks, verified formats

## Context and Problem Statement

The toolkit ships as one self-contained `skills/adr-toolkit/` package usable by multiple harnesses (Claude Code, Codex CLI, Gemini CLI, Antigravity CLI). Every harness format actually investigated expects a sibling `skills/` directory next to its own manifest file, but duplicating the package once per harness would violate the single-source-of-truth goal that motivated the self-contained package in the first place. Separately, the exact manifest fields for three of the four harnesses were never verified against real documentation before Plan 4 — and guessing already produced a real bug once (Plan 1's Claude Code adapter guessed a `"skills"` key and a nested manifest path that turned out wrong, caught only by that plan's final review).

## Decision Drivers

* Keep one canonical `skills/adr-toolkit/` package across harnesses.
* Preserve Windows-compatible tracked repository contents.
* Require manifest claims to be backed by documentation or an executable install check.
* Keep adapter-specific setup visible instead of hiding it in generated copies.

## Considered Options

* Copy the full `skills/adr-toolkit/` package into each `adapters/<harness>/` directory
* Symlink `skills/adr-toolkit/` into each adapter directory and commit the symlink to git
* Document the symlink as a manual install-time step (never committed), and verify each harness's real manifest format against its actual documentation before writing it

## Decision Outcome

Chosen option: **document the symlink as an install-time step, with formats verified not guessed**, because copying reintroduces drift between copies, committing a symlink breaks on a Windows checkout without `core.symlinks` enabled (this repo's own CI matrix includes `windows-latest`), and guessing manifest formats already produced two real bugs (Claude Code in Plan 1, Codex CLI in Plan 4) that only an actual install-and-run caught.

## Consequences

* Good: one canonical copy of the skill package exists; no manifest format ships without being checked against real documentation or a real install attempt where a harness CLI was available.
* Bad: a user must run one extra manual `ln -s` step before an adapter works — installation cannot be a true zero-step "clone and go."

## Pros and Cons of the Options

### Copy the package into every adapter

* Good, because each adapter directory is self-contained after checkout.
* Bad, because duplicated skill code and documentation can drift between harnesses.

### Commit adapter-local symlinks

* Good, because every adapter references the canonical package without copying it.
* Bad, because Windows checkout behavior depends on Git and filesystem symlink support.

### Create symlinks at install time and verify manifest formats

* Good, because the repository retains one source of truth and each harness contract can be tested independently.
* Bad, because installation includes an explicit platform-sensitive setup step and its documentation must remain accurate.

## Confirmation

`git ls-tree` on any `adapters/<harness>/` directory shows no `120000` (symlink) mode entries; every adapter's `README.md` documents the symlink as an install step; `.gitignore` ignores each adapter's `skills/` path.

## Confirmed Evidence

The tracked adapter directories contain manifests and README files but no
committed adapter-local `skills/` symlinks. The repository ignore rules exclude
those install-time paths, and the test suite checks the supported manifest
shapes. This record was reconstructed after the adapter packaging work.

## Inferred Rationale

The preference for install-time links is inferred from the observed
single-source package layout, the cross-platform CI matrix, and review notes
that corrected guessed manifest fields.

## Unknown

The original option weighting and the exact manual verification performed for
every harness version were not captured uniformly. Adapter claims must
therefore continue to distinguish executable verification from structural
layout checks.

## Revisit Triggers

* A harness's real plugin format later supports referencing an external path directly, removing the need for that harness's symlink step — revisit that harness's adapter specifically, not this policy as a whole.
