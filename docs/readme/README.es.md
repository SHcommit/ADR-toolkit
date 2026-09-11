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

ADR Toolkit es una herramienta Architecture Decision Record nativa para
agentes. Inspecciona primero el repositorio y las decisiones existentes,
pregunta solo lo necesario, registra nuevas decisiones como MADR aprobado y
compara diffs con las reglas `constraints:` de los ADR Accepted.

## Funciones

| Operation | Descripcion |
|---|---|
| **INIT** | Inicializa `docs/decisions/`, la plantilla y ADR-0001. |
| **DISCOVER** | Busca en manifests, codigo y git history decisiones historicas no documentadas, y prepara borradores de ADR para aprobar. |
| **RECORD** | Registra una nueva decision tras inspeccionar el codigo, con un maximo de 3 preguntas. |
| **CHECK** | Compara un diff con `constraints:` de ADR Accepted e informa Related / Review required / Verified violation / No applicable constraint. |

## Instalacion

`skills/adr-toolkit/` es un paquete autocontenido. Copialo o crea un symlink
en el lugar donde tu harness busca skills, y sigue el README del adapter
correspondiente.

| Harness | Install |
|---|---|
| Claude Code | [`.claude-plugin/`](../../.claude-plugin/) |
| Codex CLI | [`adapters/codex/README.md`](../../adapters/codex/README.md) |
| Gemini CLI | [`adapters/gemini-cli/README.md`](../../adapters/gemini-cli/README.md) |
| Antigravity CLI | [`adapters/antigravity/README.md`](../../adapters/antigravity/README.md) |
| Cline CLI | [`adapters/cline/README.md`](../../adapters/cline/README.md) |
| Generic | [`adapters/generic/README.md`](../../adapters/generic/README.md) |

Sin AI harness tambien puedes usar la CLI interactiva.

```bash
python skills/adr-toolkit/scripts/adr.py create --interactive --dir docs/decisions --json
```

## Idioma y configuracion del repositorio

El texto deterministico del nucleo de la herramienta admite 8 locales:
`en`, `ko`, `ja`, `zh`, `fr`, `es`, `de`, `pt-BR`.

```bash
python skills/adr-toolkit/scripts/adr.py init --locale es --dir docs/decisions --json
```

Este comando crea `.adr-toolkit.json` en la raiz del repositorio. Los comandos
siguientes usan el locale por defecto del repositorio. Un `--locale` explicito
lo reemplaza para una sola operacion.

## Alcance

- Usa el formato MADR 4.x; no crea un nuevo estandar.
- CHECK evalua solo evidencia estructural expresable mediante `constraints:`.
- INIT, CREATE e INDEX generan salida deterministica en 8 locales.
- El trabajo fuera del MVP se registra en [`project-roadmap.md`](../../project-roadmap.md).

## Contribuir

Lee primero [`AGENTS.md`](../../AGENTS.md). Contiene las reglas comunes de
trabajo y la politica de ramas del repositorio.

## Licencia

[MIT](../../LICENSE)
