---
id: ADR-0006
title: Localize deterministic ADR generation through repository configuration
status: accepted
date: 2026-08-30
locale: en
decision_makers:
  - YangSeungHyun
related:
  - ADR-0003
affected_paths:
  - .adr-toolkit.json
  - skills/adr-toolkit/SKILL.md
  - skills/adr-toolkit/schemas/adr.schema.json
  - skills/adr-toolkit/scripts/adr.py
  - skills/adr-toolkit/scripts/core/config.py
  - skills/adr-toolkit/scripts/core/locale.py
  - skills/adr-toolkit/scripts/core/rendering.py
  - skills/adr-toolkit/scripts/core/identifiers.py
  - skills/adr-toolkit/scripts/core/schema.py
  - skills/adr-toolkit/scripts/i18n/
  - skills/adr-toolkit/scripts/commands/init.py
  - skills/adr-toolkit/scripts/commands/create.py
  - skills/adr-toolkit/scripts/commands/index.py
  - skills/adr-toolkit/scripts/commands/validate.py
tags:
  - i18n
  - configuration
  - architecture
  - v0.2.0
retrospective: false
supersedes:
  - ADR-0003
---

# Localize deterministic ADR generation through repository configuration

## Context and Problem Statement

ADR-0003 limited localization to INDEX-owned strings. That MVP boundary left INIT and CREATE structures in English, required repeated locale flags, and rejected titles containing no ASCII characters. Teams need a repository-owned default language while retaining deterministic IDs, filenames, schema validation, lifecycle transitions, and CHECK behavior.

## Decision Drivers

* Keep repository state deterministic even when an agent assists with language inference or drafting.
* Let teams choose a default ADR language without repeating a flag for every operation.
* Preserve Unicode titles and bodies while keeping filenames portable across filesystems, URLs, and Git clients.
* Keep runtime validation and the published JSON Schema consistent.
* Avoid claiming that machine translation or transliteration is deterministic.

## Considered Options

* Retain ADR-0003 and localize only INDEX output.
* Delegate all localization, translation, and filename generation to an agent.
* Localize deterministic generation through a repository config, canonical catalogs, and validated agent inputs.

## Decision Outcome

Chosen option: **localize deterministic generation through a repository config, canonical catalogs, and validated agent inputs**, because it supports team language policy without handing repository governance to probabilistic output.

The repository root may contain `.adr-toolkit.json` with `schema_version: 1` and a default `locale`. The canonical locale set is `en`, `ko`, `ja`, `zh`, `fr`, `es`, `de`, and `pt-BR`; `zh` means Simplified Chinese. CLI locale resolution is explicit CLI, then approved input draft, then repository default, then English. Agent workflows use explicit user language, then request language, then repository default, then English.

The deterministic core localizes code-owned prompts, MADR structure, initial content, and index labels. It never translates user prose. ADR frontmatter may store an optional canonical `locale`. Unicode titles and bodies are preserved, while filenames remain ASCII. An agent may propose a meaningful ASCII slug for human approval; the core validates it and otherwise derives an ASCII title slug or falls back to `decision`.

### Consequences

* Good: INIT, CREATE, VALIDATE, and INDEX behave reproducibly across eight languages using one repository default.
* Good: the agent can improve filename discoverability without gaining authority to bypass deterministic validation.
* Good: existing ADRs without locale metadata remain valid.
* Bad: eight catalogs must keep exact key parity and require terminology review as the generated structure evolves.
* Bad: a non-ASCII title without an approved semantic slug falls back to a less descriptive `decision` filename.
* Bad: repository configuration introduces another versioned contract that must fail visibly when malformed or unsupported.

### Confirmation

* `tests/integration/test_localized_workflow.py` runs INIT, CREATE, VALIDATE, and INDEX for all eight canonical locales.
* `tests/unit/test_config.py` verifies config validation and locale precedence.
* `tests/unit/test_identifiers.py` verifies semantic slug validation and the deterministic fallback.
* `tests/unit/test_schema.py` verifies runtime and JSON Schema locale parity.

## Pros and Cons of the Options

### Retain INDEX-only localization

* Good, because it keeps the translation surface small.
* Bad, because repository defaults, localized creation, and non-ASCII title workflows remain unsupported.

### Delegate localization and filenames entirely to an agent

* Good, because an agent can infer language and propose natural semantic filenames.
* Bad, because repository state would depend on non-deterministic translation and transliteration unless every output crossed a validation boundary.

### Repository config, canonical catalogs, and validated agent inputs

* Good, because deterministic code owns configuration, catalogs, schema, IDs, and filenames while an agent assists only at the edge.
* Bad, because catalog parity and config compatibility become maintained product contracts.

## Revisit Triggers

* A supported locale needs regional variants whose terminology cannot share the current catalog.
* Teams require bilingual rendering of one ADR without creating parallel sources of truth.
* Repeated `decision` fallbacks show that the semantic-slug confirmation flow is insufficient.
* A future config format needs additional repository-wide options beyond locale and requires a schema migration.
