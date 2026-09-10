# ADR Toolkit

<p align="center">

[English](../../README.md) &nbsp;&nbsp;
[한국어](README.ko.md) &nbsp;&nbsp;
[日本語](README.ja.md) &nbsp;&nbsp;
[简体中文](README.zh.md) &nbsp;&nbsp;
[Français](README.fr.md) &nbsp;&nbsp;
[Español](README.es.md) &nbsp;&nbsp;
[Deutsch](README.de.md)

</p>

<p align="center">
  <a href="https://github.com/SHcommit/ADR-toolkit/releases/tag/v1.1.1"><img src="https://img.shields.io/badge/release-v1.1.1-0b8fd3?style=flat" alt="Release: v1.1.1" /></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-3776ab?style=flat" alt="Python: 3.10+" />
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/license-MIT-55aa00?style=flat" alt="License: MIT" /></a>
  <img src="https://img.shields.io/badge/ADR_locales-8-7a2cb8?style=flat" alt="ADR locales: 8" />
  <img src="https://img.shields.io/badge/README_languages-7-0b8f3a?style=flat" alt="README languages: 7" />
</p>

ADR Toolkit ist ein agent-native Architecture Decision Record Werkzeug. Es
untersucht zuerst das Repository und bestehende Entscheidungen, stellt nur die
notigen Fragen, schreibt neue Entscheidungen als bestatigte MADR und vergleicht
Diffs mit den `constraints:` Regeln von Accepted ADRs.

## Funktionen

| Operation | Beschreibung |
|---|---|
| **INIT** | Initialisiert `docs/decisions/`, das Template und ADR-0001. |
| **DISCOVER** | Sucht in manifests, Code und git history nach nicht dokumentierten fruheren Entscheidungen und erstellt ADR-Entwurfe zur Freigabe. |
| **RECORD** | Erfasst eine neue Entscheidung nach Code-Inspektion mit maximal 3 Fragen. |
| **CHECK** | Vergleicht einen diff mit `constraints:` aus Accepted ADRs und meldet Related / Review required / Verified violation / No applicable constraint. |

## Installation

`skills/adr-toolkit/` ist ein eigenstandiges Paket. Kopieren oder verlinken
Sie es an den Ort, an dem Ihr harness nach skills sucht, und folgen Sie dem
README des passenden adapters.

| Harness | Install |
|---|---|
| Claude Code | [`.claude-plugin/`](../../.claude-plugin/) |
| Codex CLI | [`adapters/codex/README.md`](../../adapters/codex/README.md) |
| Gemini CLI | [`adapters/gemini-cli/README.md`](../../adapters/gemini-cli/README.md) |
| Antigravity CLI | [`adapters/antigravity/README.md`](../../adapters/antigravity/README.md) |
| Cline CLI | [`adapters/cline/README.md`](../../adapters/cline/README.md) |
| Generic | [`adapters/generic/README.md`](../../adapters/generic/README.md) |

Ohne AI harness konnen Sie auch die interaktive CLI nutzen.

```bash
python skills/adr-toolkit/scripts/adr.py create --interactive --dir docs/decisions --json
```

## Sprache und Repository-Konfiguration

Deterministisch erzeugter Text unterstutzt 8 locales:
`en`, `ko`, `ja`, `zh`, `fr`, `es`, `de`, `pt-BR`.

```bash
python skills/adr-toolkit/scripts/adr.py init --locale de --dir docs/decisions --json
```

Dieser Befehl erstellt `.adr-toolkit.json` im Repository-Root. Danach nutzen
Befehle die Repository-Standardsprache. Ein explizites `--locale` uberschreibt
sie fur genau eine Operation.

## Umfang

- Es wird MADR 4.x verwendet; kein neuer Standard wird eingefuhrt.
- CHECK bewertet nur strukturelle Evidenz, die durch `constraints:` ausdruckbar ist.
- INIT, CREATE und INDEX liefern deterministische Ausgabe in 8 locales.
- Arbeit ausserhalb des MVP wird in [`project-roadmap.md`](../../project-roadmap.md) verfolgt.

## Beitragen

Lesen Sie zuerst [`AGENTS.md`](../../AGENTS.md). Dort stehen die gemeinsamen
Arbeitsregeln und die Branch-Policy des Repositories.

## Lizenz

[MIT](../../LICENSE)
