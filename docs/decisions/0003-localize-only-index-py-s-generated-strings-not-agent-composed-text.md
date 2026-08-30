---
id: ADR-0003
title: Localize only index.py's generated strings, not agent-composed text
status: accepted
date: 2026-08-30
decision_makers:
  - YangSeungHyun
locale: en
related: []
affected_paths:
  - .adr-toolkit.json
  - skills/adr-toolkit/SKILL.md
  - skills/adr-toolkit/scripts/core/locale.py
  - skills/adr-toolkit/scripts/core/config.py
  - skills/adr-toolkit/scripts/core/rendering.py
  - skills/adr-toolkit/scripts/i18n/
  - skills/adr-toolkit/scripts/commands/init.py
  - skills/adr-toolkit/scripts/commands/create.py
  - skills/adr-toolkit/scripts/commands/index.py
tags:
  - i18n
  - architecture
retrospective: true
---

# Localize only index.py's generated strings, not agent-composed text

## Context and Problem Statement

The product goal is five-language support (en/fr/ja/ko/zh). The original design's repo-structure diagram proposed a flat `scripts/i18n/{locale}.json` key-value file, but most of the toolkit's user-facing text — RECORD/DISCOVER/CHECK's interview questions and reports — is agent-composed natural language, not a fixed Python string. It is not obvious what a translation-key file would even contain for text that is never the same twice.

## Considered Options

* A comprehensive translation-key system covering every user-facing string, including agent-composed prose, requiring the agent to look up keys instead of composing text freely
* Localize only the deterministic, code-owned strings — `index.py`'s generated `README.md` headers and status labels — via a small JSON file, and instruct the agent (via `SKILL.md`) to detect the user's language and compose its own text in it

## Decision Outcome

Chosen option: **localize only index.py's generated strings**, because an LLM agent is already multilingual and needs no phrase-book to ask a question in French — building and maintaining a lookup table for text that was never a fixed string in the first place adds real translation-maintenance burden for no benefit.

## Consequences

* Good: only ten keys need translating and keeping in sync across five locales, not hundreds of agent-prose variants.
* Bad: the agent's exact wording is not guaranteed reproducible or testable per locale the way a translation table's output would be.

## Confirmation

`skills/adr-toolkit/scripts/i18n/*.json` has exactly ten keys per locale; `SKILL.md`'s Language section is the only agent-facing localization instruction, and it is prose, not a lookup table.

## Confirmed Evidence

The v0.1.0 implementation localized only INDEX-owned headings and status labels
through five JSON catalogs. INIT and CREATE still emitted English structure,
and there was no repository locale configuration. This ADR was reconstructed
after that implementation existed.

## Inferred Rationale

The motivation recorded above is inferred from the original narrow
implementation and design notes: avoid translating open-ended agent prose while
keeping the deterministic code surface small.

## Unknown

The original discussion did not preserve a complete comparison of
repository-level defaults, localized deterministic templates, or multilingual
filename behavior. Those omissions later became the reason to revisit this
decision for v0.2.0.

## Revisit Triggers

* The tool needs deterministic, exact-wording compliance per locale (for example, an accessibility or compliance audit) — revisit toward a full translation-key system at that point.
