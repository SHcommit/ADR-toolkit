# OSS Repository Governance Audit

검증 기준일: 2026-09-06 (Asia/Seoul)

이 보고서는 파일 존재 여부뿐 아니라 backlog가 수백~수천 건으로 늘어났을 때
한 명의 maintainer가 반복 분류·보안 점검·merge 통제를 감당할 수 있는지를
기준으로 작성했다. 로컬 브랜치의 구성과 GitHub API로 조회한 live 설정을
구분한다.

## 1. Executive Summary

ADR Toolkit은 문서, 테스트, release provenance, 다중 플랫폼 CI가 이미 강한
소형 OSS 저장소다. 이번 hardening으로 label taxonomy, path labeler,
Dependabot, Issue Forms, lint, dependency audit, dormant CODEOWNERS를 추가했고,
live repository에는 Discussions, 보안 알림, 자동 security update, secret
scanning/push protection, private vulnerability reporting을 활성화했다.

가장 중요한 리뷰 결과는 기존 감사의 전제 오류다. Classic branch-protection
API가 404를 반환했지만 repository ruleset은 2026-09-02부터 active였다.
Ruleset `22101891`은 `master`/`develop`/`release/*`에 PR, required checks,
conversation resolution, deletion/non-fast-forward 차단을 적용하고, ruleset
`22102322`는 `v*` tag 수정·삭제를 차단한다. 실제 남은 위험은 보호 규칙의
부재가 아니라 CI matrix 변경 후 required-check 이름이 drift하는 것이다.

현재 운영 수준은 **🟢 성장 가능한 기본 구조, 단 rollout 1단계 필요**로
평가한다. 이 브랜치를 `develop`에 merge한 직후 ruleset에서 Python 3.9 check를
3.10 check로 교체하고 `lint`/`dependency-audit`를 required로 추가해야 한다.

## 2. Repository Audit

| 영역 | 현재 상태 | 문제 또는 근거 | 우선순위 |
| --- | --- | --- | --- |
| README | 🟢 충분함 | 설치, 기능, scope, 기여 링크 제공 | P2 |
| CONTRIBUTING | 🟢 충분함 | Git Flow, local checks, ADR/adapter 규칙 제공 | P2 |
| CODE_OF_CONDUCT | 🟢 충분함 | 행동 기준·신고·집행 범위 명시 | P2 |
| SECURITY | 🟢 충분함 | private advisory 경로, 지원 버전, checksum/attestation 검증 제공 | P1 |
| LICENSE | 🟢 충분함 | MIT license 존재 | P2 |
| CHANGELOG | 🟢 충분함 | `Unreleased`와 release별 human-readable 기록 | P2 |
| Roadmap | 🟢 충분함 | trigger 기반 deferred work와 완료 항목 구분 | P2 |
| ADR / architecture docs | 🟢 충분함 | `docs/decisions/`와 설계·감사 문서 존재 | P2 |
| Issue templates | 🟢 충분함 | bug/feature Issue Forms와 blank issue 차단 | P1 |
| PR template | 🟢 충분함 | Conventional title, ADR/example 영향 확인 | P1 |
| Labels | 🟢 충분함 | 25개 source taxonomy 중 type/area/priority/size/workflow 20개를 live sync 완료 | P1 |
| GitHub Projects | 🟡 개선 필요 | 기능은 enabled지만 Project 없음; open issue 0개라 지금 생성은 과함 | NEXT |
| Milestones | 🟡 개선 필요 | milestone 없음; release backlog가 생길 때 도입 | NEXT |
| CODEOWNERS | 🟡 개선 필요 | dormant draft 존재, 1인 maintainer라 required review는 의도적으로 OFF | NEXT |
| Discussions | 🟢 충분함 | live 활성화 및 Q&A category 확인 | P1 |
| Branch/tag ruleset | 🟡 개선 필요 | active/effective 확인; required checks는 아직 Python 3.9 이름을 포함 | P0 rollout |
| Merge 정책 | 🟢 충분함 | PR 강제와 merge 후 short-lived branch 자동 삭제 활성화 | P1 |
| Build | 🟢 충분함 | release에서 wheel/sdist와 skill archive 생성 | P1 |
| Test | 🟢 충분함 | unit+integration 550+ cases | P1 |
| Lint | 🟢 충분함 | ruff E9/F fast gate 추가 | P1 |
| Type check | 🟢 충분함 | 핵심 typed module에 mypy `--strict` | P1 |
| Coverage | 🟢 충분함 | branch coverage 85% floor | P1 |
| Multi-platform | 🟢 충분함 | Linux/macOS/Windows × Python 3.10/3.12 | P1 |
| E2E | 🟢 충분함 | Codex/Gemini/Antigravity adapter install-and-run | P1 |
| Release | 🟡 개선 필요 | direct-tag workflow와 version gate 있음; PyPI publish는 `continue-on-error` | P1 |
| Artifact verification | 🟢 충분함 | SHA-256 release asset과 version/tag drift gate | P1 |
| Provenance / attestation | 🟢 충분함 | public release에 GitHub Artifact Attestation | P1 |
| Changelog requirement | 🟡 개선 필요 | template/process는 있으나 자동 path-based gate 없음 | NEXT |
| Documentation drift | 🟢 충분함 | examples execution/drift gate 제공 | P1 |
| Dependabot | 🟢 충분함 | pip/actions weekly grouped PR, target `develop` | P1 |
| GitHub Actions pinning | 🟡 개선 필요 | write-capable release actions는 SHA pin; read-only CI first-party actions는 major pin | P2 |
| Remote installer | 🟢 충분함 | Antigravity fixed artifact + official SHA-512 verification, `curl | bash` 제거 | P0 |
| Package lock | 🟡 개선 필요 | runtime dependency 0개; dev tools exact pin이라 lock 부재 위험은 제한적 | P2 |
| Dependency/security audit | 🟢 충분함 | `pip-audit --strict`, alerts/security updates/secret scanning enabled | P1 |

## 3. NOW

- 완료: `.github/labels.yml`과 live label taxonomy 동기화.
- 완료: changed path 기반 PR labeler와 new issue `needs-triage` 적용.
- 완료: structured Issue Forms와 Discussions/Q&A 경로.
- 완료: pip/GitHub Actions Dependabot을 weekly grouped update로 구성하고
  `develop`을 target branch로 고정.
- 완료: ruff lint와 `pip-audit --strict` CI gate.
- 완료: Antigravity CI installer를 versioned artifact + SHA-512 검증으로 교체.
- 완료: release workflow dependency pin 및 write-capable workflow Action SHA pin.
- 완료: vulnerability alerts, automated security fixes, secret scanning,
  push protection, private vulnerability reporting 활성화.
- rollout 직후: ruleset required contexts에서 Python 3.9 두 개를 제거하고
  Python 3.10 세 개, `lint`, `dependency-audit`를 추가.

## 4. NEXT

- Issue가 약 20~30개 이상 지속되거나 동시에 진행 중인 work item이 10개를
  넘으면 Project를 만든다.
- 2명 이상의 qualified maintainer가 생기면 dormant CODEOWNERS를 영역별로
  분리하고 code-owner review를 required로 전환한다.
- PR queue가 10개 이상 지속될 때 `size:XS`~`size:XL` 자동 분류를 추가한다.
- release 목표 issue가 5개 이상 모이면 milestone을 source of truth로 쓴다.
- ruleset check-context drift가 다시 발생하면 settings verification script나
  Terraform/GitHub provider 기반 ruleset-as-code를 도입한다.

권장 수동 size 기준은 XS 10 LOC 이하, S 50 이하, M 200 이하, L 500 이하,
XL 500 초과다. Generated file, security-sensitive workflow, schema 변경은 LOC와
무관하게 한 단계 상향할 수 있다.

## 5. LATER

- stale bot: abandoned backlog가 실제로 누적된 뒤에만 도입한다. 기준은
  90일 inactive → stale, 추가 30일 → close이며 `security`, `pinned`,
  `roadmap`, `help wanted`, `priority:P0`, `blocked`는 제외한다.
- organization ruleset/reusable workflow/RBAC/audit export: 동일 운영을
  반복하는 repository가 2개 이상일 때 도입한다.
- ML triage, automatic assignment, 복잡한 release train은 현재 도입하지 않는다.

## 6. Security / Supply Chain Findings

1. **해결 — remote code execution:** `curl install.sh | bash`가 실제 PR CI에서
   실행되고 있었다. 공식 manifest가 가리킨 Antigravity CLI `1.1.27` Linux
   artifact URL과 SHA-512를 고정해 다운로드·검증·설치 단계로 분리했다.
2. **해결 — release mutability:** `release.yml`의 Action ref를 현재 commit SHA로
   고정하고 version comment를 남겼다. Python build/test tool도 dev extra pin을
   사용한다.
3. **해결 — dependency visibility:** Dependabot security updates와 alerts,
   `pip-audit --strict`, secret scanning/push protection을 활성화했다.
4. **해결 — PR title command injection:** untrusted PR title expression을 inline
   shell 문자열에 삽입하지 않고 step environment로 전달하도록 변경했다.
5. **남음 — partial release:** PyPI publish가 `continue-on-error: true`라 GitHub
   Release 성공과 PyPI 실패가 동시에 가능하다. Trusted Publisher 안정성이
   확인되면 fail-closed 전환을 검토한다.
6. **수용 — read-only CI Action tags:** 일반 test/labeler의 GitHub-owned Actions는
   major tag를 사용한다. Release처럼 write 권한을 갖는 경로는 SHA pin을 적용했다.

## 7. 추가/수정 파일

```text
.github/
├── CODEOWNERS
├── dependabot.yml
├── labeler.yml
├── labels.yml
├── ISSUE_TEMPLATE/
│   ├── bug_report.yml
│   ├── feature_request.yml
│   └── config.yml
└── workflows/
    ├── labeler.yml
    ├── labels.yml
    ├── release.yml
    └── test.yml
scripts/
└── export_dev_requirements.py
tests/unit/
└── test_github_governance.py
```

각 파일의 실행 가능한 실제 내용은 위 경로 자체가 source of truth다. 추가로
`pyproject.toml`, `SECURITY.md`, `project-roadmap.md`,
`docs/enterprise-adoption.md`, 본 설계 문서를 현재 운영 상태에 맞게 수정했다.

## 8. GitHub UI 설정

API로 확인/적용한 live 상태:

- Discussions: enabled.
- Repository Projects: enabled, Project instance는 없음.
- Dependabot security updates: enabled.
- Vulnerability alerts: enabled.
- Secret scanning / push protection: enabled.
- Private vulnerability reporting: enabled.
- Delete branch on merge: enabled.
- Branch ruleset `22101891`: active, bypass actor 없음.
- Tag ruleset `22102322`: active, bypass actor 없음.

이 브랜치 merge 직후 Settings → Rules → Rulesets에서 `protected-branches`의
required checks를 다음과 같이 맞춘다.

```text
remove: pytest (ubuntu-latest, 3.9)
remove: pytest (windows-latest, 3.9)
add:    pytest (ubuntu-latest, 3.10)
add:    pytest (macos-latest, 3.10)
add:    pytest (windows-latest, 3.10)
add:    lint
add:    dependency-audit
keep:   all Python 3.12 checks, type-check, version-drift,
        examples-drift, pr-title-check, harness-parity
```

Required approving review count와 code-owner review는 maintainer가 1명인 동안
0/OFF를 유지한다. Signed commits도 현재는 요구하지 않는다.

## 9. Issue Backlog 후보

| 후보 | 출처 | 추천 labels | 크기 |
| --- | --- | --- | --- |
| `adapters/README.md`에 “새 harness adapter 추가하기” tutorial 작성 | `docs/adr-toolkit-audit-report.md` §2.6 | `type:docs`, `area:adapter`, `good first issue` | S |
| harness parity를 `check/search/graph/create`까지 확장 | `project-roadmap.md` Harness parity | `type:test`, `area:adapter`, `help wanted` | M |
| 실제 사용자 피드백 후 Traditional Chinese `zh-TW` catalog 검토 | `project-roadmap.md` Internationalization | `type:feature`, `area:core`, `help wanted` | M |
| Accepted ADR metadata factual-correction policy 설계 | `project-roadmap.md` Lifecycle research | `type:docs`, `area:docs`, `priority:P2` | M |
| ruleset required-check drift 자동 검증 | 이번 감사의 재발 방지 항목 | `type:test`, `area:github`, `priority:P1` | S |

첫 good-first issue는 문서 tutorial이 가장 적합하다. Product behavior를 바꾸지
않고 기존 adapter를 비교해 명확한 acceptance criteria를 만들 수 있다.

## 10. 최종 목표 구조

```text
Idea
 ↓
Issue Form / Discussion
 ↓
Auto Triage / Label
 ↓
Issue backlog (Project는 규모 trigger 충족 시)
 ↓
Contributor
 ↓
Pull Request
 ↓
Automated Quality Gates
 ↓
Review + conversation resolution
 ↓
Merge to develop
 ↓
Release branch → master → v* tag
 ↓
Attestation / checksum / dependency & security maintenance
```

목표는 자동화 개수가 아니라 maintainer 판단이 필요한 우선순위·설계·review만
사람에게 남기고, 입력 구조화·경로 분류·반복 검증·dependency 감시는 GitHub와
CI가 수행하게 하는 것이다.
