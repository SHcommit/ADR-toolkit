# 릴리스 아티팩트 공급망 보안(Build Provenance Attestation) 도입

## 날짜

2026-09-01

## 문제 상황

`docs/adr-toolkit-audit-report.md` §2.2 2.2 감사 항목이 "공급망 보안
체크섬/서명 부재"를 지적했다. `.github/workflows/release.yml`은 테스트
실행, 매니페스트 버전 동기화 검사(`sync_version.py --check`), 태그==
`VERSION` 일치 검증까지만 하고 `softprops/action-gh-release@v2`로
릴리스를 생성할 뿐, 릴리스에 첨부되는 어떤 아티팩트도 체크섬이나
서명이 없었다.

## 기존 구조나 방식의 한계

일반적인 npm/PyPI 프로젝트라면 "빌드 산출물을 체크섬 찍고 Sigstore로
서명"하는 패턴이 바로 적용된다. 하지만 이 프로젝트는 빌드 산출물
자체가 없다 — Claude Code 마켓플레이스(`marketplace.json`의
`source: "./"`), Codex/Gemini CLI 플러그인 설치, 일반 copy/symlink 설치
전부 git 저장소나 `skills/adr-toolkit/` 폴더를 **직접** 참조한다.
즉 "체크섬/서명할 아티팩트가 무엇인가"부터 정의되지 않은 상태였고,
감사 보고서의 원안(빌드 아티팩트를 체크섬+서명)을 그대로 옮기면
아무도 실제로 소비하지 않는 파일에 서명하는 형식적 조치가 될
위험이 있었다.

## 관련 코드 맥락

- `.github/workflows/release.yml` — `v*` 태그 push 시 실행되는 유일한
  릴리스 파이프라인. 기존에는 `permissions: contents: write`만 있었고
  패키징 스텝이 전혀 없었다.
- `AGENTS.md`에 문서화된 릴리스 프로세스: 버전 태그는 **사람이 로컬에서
  직접 생성**한 뒤 push한다. 즉 CI는 이미 push된 태그를 사후에 서명할
  방법이 없다(태그 자체에 서명하려면 로컬 GPG 서명 절차가 별도로
  필요하며, 이는 CI 워크플로 범위 밖).
- `SECURITY.md` — 취약점 신고 프로세스만 있고 릴리스 검증 방법에 대한
  섹션이 없었다.

## 검토한 선택지

1. **빌드 아티팩트 없음 + git 태그 자체에 서명(GPG)** — 태그가 로컬에서
   사람이 만들기 때문에 CI 워크플로 안에서는 구현 불가. 기각.
2. **`skills/adr-toolkit/`를 tar.gz로 패키징 + 체크섬만** — 전송 중
   손상은 잡지만 "진짜 이 저장소의 CI가 만들었는가"라는 provenance는
   증명하지 못함.
3. **tar.gz 패키징 + SHA-256 체크섬 + GitHub Artifact Attestation
   (`actions/attest-build-provenance@v2`)** — Sigstore 기반 keyless
   서명이라 개인키 관리/로테이션이 전혀 없고, GitHub Actions OIDC 토큰으로
   "이 커밋의 이 워크플로 실행이 만든 파일"이라는 provenance를 증명한다.
4. **자체 GPG 키를 리포지토리 시크릿으로 관리해 아티팩트 서명** — 개인키
   보관/로테이션 부담이 있고, 이 프로젝트처럼 유지관리자가 1인인
   상황에서는 키 손실/유출 리스크만 늘어남. 기각.

## 판단 기준

- 실제 소비 경로(거의 모든 설치가 git repo/스킬 폴더 직접 참조)를
  기준으로, "아무도 받지 않는 아티팩트에 서명"하는 헛수고를 피한다.
- CI가 사후에 할 수 있는 일만 범위에 넣는다 — 태그 서명처럼 이미
  일어난 사람의 행동을 CI가 대신할 수 없는 것은 배제.
- 개인키를 만들거나 로테이션하는 운영 부담을 새로 만들지 않는다(1인
  운영 프로젝트라는 현재 상태를 고려).

## 최종 결정

옵션 3 — tar.gz 패키징 + SHA-256 체크섬 + GitHub Artifact Attestation.
GitHub Releases 페이지에서 직접 아카이브를 내려받는 소수의 경로에 대해
"이 파일이 이 저장소의 이 커밋에서 만들어졌다"는 provenance를 keyless로
증명하고, 나머지(git clone/plugin install 경로)는 기존처럼 Git/GitHub
자체의 커밋 이력으로 신뢰성을 확보한다는 점을 `SECURITY.md`에 명시했다.

## 해결 방식

1. `.github/workflows/release.yml`의 `permissions`에 `id-token: write`,
   `attestations: write` 추가(OIDC 토큰 발급 + attestation 게시 권한).
2. "Package the distributable skill" 스텝 추가: `VERSION` 파일을 읽어
   `adr-toolkit-skill-v${VERSION}.tar.gz`로 `skills/adr-toolkit`를
   패키징하고 `sha256sum`으로 체크섬 파일 생성, `$GITHUB_OUTPUT`으로
   아카이브 경로를 다음 스텝에 전달.
3. "Generate build provenance attestation" 스텝 추가:
   `actions/attest-build-provenance@v2`에 `subject-path`로 방금 만든
   아카이브 경로를 전달.
4. "Create GitHub Release" 스텝의 `files:`에 아카이브와 `.sha256` 파일을
   함께 첨부.
5. `SECURITY.md`에 "Verifying a Release" 섹션 신설 — `sha256sum -c`와
   `gh attestation verify <archive> -R SHcommit/ADR-toolkit` 명령, 그리고
   git clone/adapter 설치 경로는 이 아카이브 검증과 무관하다는 점을 명시.

## 결과

- 커밋 `18d4662` (`feat: add build provenance attestation to the release
  workflow`).
- YAML 문법 검증 통과, 전체 테스트 스위트(`pytest tests/unit
  tests/integration`) 541 passed로 회귀 없음 확인.
- 실제 OIDC 기반 attestation 발급/검증 플로우 자체는 GitHub Actions
  러너에서 실제 `v*` 태그 push가 일어나야만 최종 확인 가능 — 로컬에서는
  워크플로 문법과 각 스텝의 셸 로직만 검증했다. 다음 실제 릴리스
  태그(예: 다음 버전 bump) 때 `gh attestation verify`로 실물 검증 필요.
- 병렬로 진행 중이던 Codex 세션의 도입 지표(adoption metrics) 수집기
  작업(`9a0de45`..`f814d64`, `scripts/adoption_metrics.py`)은 이
  세션과 무관하게 이미 완료되어 있었음 — 이 작업으로 인한 충돌은
  없었다.
