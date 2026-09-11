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

ADR Toolkit은 agent-native Architecture Decision Record 도구입니다. 저장소와
기존 결정을 먼저 살펴본 뒤 질문하고, 승인된 MADR 형식으로 새 결정을 기록하며,
Accepted ADR의 `constraints:` 규칙과 diff를 비교해 구조적 충돌을 확인합니다.

## 하는 일

| Operation | 설명 |
|---|---|
| **INIT** | `docs/decisions/` 디렉터리, 템플릿, ADR-0001을 초기화합니다. |
| **DISCOVER** | 매니페스트, 코드, git history에서 과거의 암묵적 결정을 찾아 회고 ADR 초안을 만듭니다. |
| **RECORD** | 새 결정을 기록합니다. 코드 조사를 먼저 하고, 확인이 필요한 내용만 최대 3개 질문합니다. |
| **CHECK** | diff를 Accepted ADR의 `constraints:`와 비교해 Related, Review required, Verified violation, No applicable constraint를 보고합니다. |

## 설치

`skills/adr-toolkit/`은 자체 완결형 패키지입니다. 사용하는 harness가 skill을
찾는 위치로 복사하거나 symlink한 뒤, 해당 adapter README를 따르세요.

| Harness | Install |
|---|---|
| Claude Code | [`.claude-plugin/`](../../.claude-plugin/) |
| Codex CLI | [`adapters/codex/README.md`](../../adapters/codex/README.md) |
| Gemini CLI | [`adapters/gemini-cli/README.md`](../../adapters/gemini-cli/README.md) |
| Antigravity CLI | [`adapters/antigravity/README.md`](../../adapters/antigravity/README.md) |
| Cline CLI | [`adapters/cline/README.md`](../../adapters/cline/README.md) |
| Generic | [`adapters/generic/README.md`](../../adapters/generic/README.md) |

AI harness 없이도 interactive CLI를 사용할 수 있습니다.

```bash
python skills/adr-toolkit/scripts/adr.py create --interactive --dir docs/decisions --json
```

## 언어와 저장소 설정

도구가 결정적으로 생성하는 텍스트는 여덟 locale을 지원합니다:
`en`, `ko`, `ja`, `zh`, `fr`, `es`, `de`, `pt-BR`.

```bash
python skills/adr-toolkit/scripts/adr.py init --locale ko --dir docs/decisions --json
```

이 명령은 저장소 루트에 `.adr-toolkit.json`을 만들고, 이후 명령은 저장소
기본 locale을 사용합니다. 명시적 `--locale` 플래그가 있으면 한 번의 작업에
대해 기본값을 덮어씁니다.

## 범위

- MADR 4.x 형식을 사용하며 새 표준을 만들지 않습니다.
- CHECK는 `constraints:` 블록으로 표현 가능한 구조적 증거만 평가합니다.
- INIT, CREATE, INDEX의 결정적 출력은 여덟 locale로 제공됩니다.
- MVP 이후 작업은 [`project-roadmap.md`](../../project-roadmap.md)에 기록합니다.

## 기여

먼저 [`AGENTS.md`](../../AGENTS.md)를 읽어 주세요. 이 저장소에서 사용하는
공통 작업 규칙과 브랜치 정책이 들어 있습니다.

## 라이선스

[MIT](../../LICENSE)
