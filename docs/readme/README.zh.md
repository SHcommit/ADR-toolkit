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

ADR Toolkit 是面向 agent 的 Architecture Decision Record 工具。它会先检查
仓库和已有决策，再提出问题；用经过人工确认的 MADR 记录新决策；并把 diff
与 Accepted ADR 中的 `constraints:` 规则进行比较，报告结构性冲突。

## 功能

| Operation | 说明 |
|---|---|
| **INIT** | 初始化 `docs/decisions/`、模板和 ADR-0001。 |
| **DISCOVER** | 从 manifest、代码和 git history 中发现未记录的历史决策，并生成可审阅的 ADR 草稿。 |
| **RECORD** | 记录新的决策。先检查代码，只对无法确认的信息最多提出 3 个问题。 |
| **CHECK** | 将 diff 与 Accepted ADR 的 `constraints:` 比较，并报告 Related / Review required / Verified violation / No applicable constraint。 |

## 安装

`skills/adr-toolkit/` 是自包含包。将它复制或 symlink 到你的 harness 查找
skills 的位置，然后按照对应的 adapter README 操作。

| Harness | Install |
|---|---|
| Claude Code | [`.claude-plugin/`](../../.claude-plugin/) |
| Codex CLI | [`adapters/codex/README.md`](../../adapters/codex/README.md) |
| Gemini CLI | [`adapters/gemini-cli/README.md`](../../adapters/gemini-cli/README.md) |
| Antigravity CLI | [`adapters/antigravity/README.md`](../../adapters/antigravity/README.md) |
| Cline CLI | [`adapters/cline/README.md`](../../adapters/cline/README.md) |
| Generic | [`adapters/generic/README.md`](../../adapters/generic/README.md) |

没有 AI harness 时也可以使用 interactive CLI。

```bash
python skills/adr-toolkit/scripts/adr.py create --interactive --dir docs/decisions --json
```

## 语言和仓库配置

确定性生成的文本支持 8 个 locale:
`en`, `ko`, `ja`, `zh`, `fr`, `es`, `de`, `pt-BR`。

```bash
python skills/adr-toolkit/scripts/adr.py init --locale zh --dir docs/decisions --json
```

该命令会在仓库根目录创建 `.adr-toolkit.json`。之后的命令会使用仓库默认
locale。显式 `--locale` 参数只会覆盖当前一次操作。

## 范围

- 使用 MADR 4.x 格式，不创建新的标准。
- CHECK 只评估可由 `constraints:` 块表达的结构性证据。
- INIT、CREATE 和 INDEX 的确定性输出支持 8 个 locale。
- MVP 之后的工作记录在 [`project-roadmap.md`](../../project-roadmap.md)。

## 贡献

请先阅读 [`AGENTS.md`](../../AGENTS.md)。其中包含本仓库的通用工作规则和分支策略。

## 许可证

[MIT](../../LICENSE)
