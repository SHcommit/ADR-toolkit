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

ADR Toolkit は agent-native な Architecture Decision Record ツールです。
リポジトリと既存の決定を先に調べ、必要な質問を行い、承認済みの MADR として
新しい決定を記録します。また Accepted ADR の `constraints:` と diff を照合し、
構造的な衝突を確認します。

## 機能

| Operation | 説明 |
|---|---|
| **INIT** | `docs/decisions/`、テンプレート、ADR-0001 を初期化します。 |
| **DISCOVER** | manifest、コード、git history から未記録の過去決定を探し、承認対象の ADR 草案を作ります。 |
| **RECORD** | 新しい決定を記録します。先にコードを調べ、不足情報だけを最大 3 問質問します。 |
| **CHECK** | diff を Accepted ADR の `constraints:` と照合し、Related / Review required / Verified violation / No applicable constraint を報告します。 |

## インストール

`skills/adr-toolkit/` は自己完結型パッケージです。利用する harness が
skill を探す場所へコピーまたは symlink し、対応する adapter README に従ってください。

| Harness | Install |
|---|---|
| Claude Code | [`.claude-plugin/`](../../.claude-plugin/) |
| Codex CLI | [`adapters/codex/README.md`](../../adapters/codex/README.md) |
| Gemini CLI | [`adapters/gemini-cli/README.md`](../../adapters/gemini-cli/README.md) |
| Antigravity CLI | [`adapters/antigravity/README.md`](../../adapters/antigravity/README.md) |
| Cline CLI | [`adapters/cline/README.md`](../../adapters/cline/README.md) |
| Generic | [`adapters/generic/README.md`](../../adapters/generic/README.md) |

AI harness がなくても interactive CLI を利用できます。

```bash
python skills/adr-toolkit/scripts/adr.py create --interactive --dir docs/decisions --json
```

## 言語とリポジトリ設定

決定的に生成されるテキストは 8 つの locale をサポートします:
`en`, `ko`, `ja`, `zh`, `fr`, `es`, `de`, `pt-BR`.

```bash
python skills/adr-toolkit/scripts/adr.py init --locale ja --dir docs/decisions --json
```

このコマンドはリポジトリルートに `.adr-toolkit.json` を作成します。以降の
コマンドはリポジトリ既定の locale を使います。明示的な `--locale` は
その 1 回の実行だけ既定値を上書きします。

## スコープ

- MADR 4.x 形式を使用し、新しい標準は作りません。
- CHECK は `constraints:` ブロックで表現できる構造的証拠のみ評価します。
- INIT、CREATE、INDEX の決定的な出力は 8 locale で提供されます。
- MVP 以降の作業は [`project-roadmap.md`](../../project-roadmap.md) に記録します。

## コントリビュート

まず [`AGENTS.md`](../../AGENTS.md) を読んでください。このリポジトリ共通の
作業ルールとブランチポリシーが書かれています。

## ライセンス

[MIT](../../LICENSE)
