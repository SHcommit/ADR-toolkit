---
id: ADR-0003
title: Localize only index.py's generated strings, not agent-composed text
status: accepted
date: 2026-08-30
decision_makers: []
related: []
affected_paths:
  - skills/adr-toolkit/scripts/core/locale.py
  - skills/adr-toolkit/scripts/i18n/
  - skills/adr-toolkit/scripts/commands/index.py
tags:
  - i18n
  - architecture
retrospective: false
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

## Revisit Triggers

* The tool needs deterministic, exact-wording compliance per locale (for example, an accessibility or compliance audit) — revisit toward a full translation-key system at that point.
