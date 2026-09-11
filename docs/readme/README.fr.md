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
  <a href="https://github.com/SHcommit/ADR-toolkit/releases/tag/v1.1.2"><img src="https://img.shields.io/badge/release-v1.1.2-0b8fd3?style=flat" alt="Release: v1.1.2" /></a>
  <img src="https://img.shields.io/badge/python-3.10%2B-3776ab?style=flat" alt="Python: 3.10+" />
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/license-MIT-55aa00?style=flat" alt="License: MIT" /></a>
  <img src="https://img.shields.io/badge/ADR_locales-8-7a2cb8?style=flat" alt="ADR locales: 8" />
  <img src="https://img.shields.io/badge/README_languages-7-0b8f3a?style=flat" alt="README languages: 7" />
</p>

ADR Toolkit est un outil Architecture Decision Record concu pour les agents.
Il inspecte d'abord le depot et les decisions existantes, pose seulement les
questions necessaires, enregistre les nouvelles decisions en MADR approuve, et
compare les diffs aux regles `constraints:` des ADR Accepted.

## Fonctionnalites

| Operation | Description |
|---|---|
| **INIT** | Initialise `docs/decisions/`, le modele et ADR-0001. |
| **DISCOVER** | Cherche dans les manifests, le code et git history les decisions passees non documentees, puis prepare des brouillons d'ADR a approuver. |
| **RECORD** | Enregistre une nouvelle decision apres inspection du code, avec au plus 3 questions. |
| **CHECK** | Compare un diff aux `constraints:` des ADR Accepted et signale Related / Review required / Verified violation / No applicable constraint. |

## Installation

`skills/adr-toolkit/` est un paquet autonome. Copiez-le ou creez un symlink
vers l'emplacement ou votre harness cherche les skills, puis suivez le README
de l'adapter correspondant.

| Harness | Install |
|---|---|
| Claude Code | [`.claude-plugin/`](../../.claude-plugin/) |
| Codex CLI | [`adapters/codex/README.md`](../../adapters/codex/README.md) |
| Gemini CLI | [`adapters/gemini-cli/README.md`](../../adapters/gemini-cli/README.md) |
| Antigravity CLI | [`adapters/antigravity/README.md`](../../adapters/antigravity/README.md) |
| Cline CLI | [`adapters/cline/README.md`](../../adapters/cline/README.md) |
| Generic | [`adapters/generic/README.md`](../../adapters/generic/README.md) |

Sans AI harness, l'interface interactive CLI reste disponible.

```bash
python skills/adr-toolkit/scripts/adr.py create --interactive --dir docs/decisions --json
```

## Langue et configuration du depot

Le texte determine par le coeur de l'outil prend en charge 8 locales:
`en`, `ko`, `ja`, `zh`, `fr`, `es`, `de`, `pt-BR`.

```bash
python skills/adr-toolkit/scripts/adr.py init --locale fr --dir docs/decisions --json
```

Cette commande cree `.adr-toolkit.json` a la racine du depot. Les commandes
suivantes utilisent la locale par defaut du depot. Un `--locale` explicite
remplace cette valeur pour une seule operation.

## Portee

- Le format MADR 4.x est utilise; aucun nouveau standard n'est cree.
- CHECK evalue uniquement les preuves structurelles exprimables par `constraints:`.
- INIT, CREATE et INDEX produisent du texte determine dans 8 locales.
- Le travail hors MVP est suivi dans [`project-roadmap.md`](../../project-roadmap.md).

## Contribution

Lisez d'abord [`AGENTS.md`](../../AGENTS.md). Il contient les regles communes
de travail et la politique de branches du depot.

## Licence

[MIT](../../LICENSE)
