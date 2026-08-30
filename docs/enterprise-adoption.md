# ADR Toolkit 엔터프라이즈 도입 보고서

작성일: 2026-08-30

범위: v0.2.0 이후의 팀·공개 저장소·조직 단위 도입

## 1. 요약

ADR Toolkit의 강점은 AI가 초안과 언어 표현을 돕더라도 repository state의 진실은
결정론적 코어가 소유한다는 점이다. 현재 구현은 개인·소규모 팀이 반복 사용할 수
있는 수준이지만, 엔터프라이즈 도구라고 부르기에는 권한, 독립 승인, 감사, 예외,
조직 정책 배포, 채택 측정이 부족하다.

가장 좋은 확장 순서는 기능을 한 번에 늘리는 것이 아니라 다음 네 단계다.

1. private solo 저장소에서 v0.2.0의 정확성을 확정한다.
2. public 전환 시 GitHub ruleset과 기본 기여 통제를 실제로 강제한다.
3. 복수 maintainer가 생기면 CODEOWNERS와 독립 ADR review를 도입한다.
4. 여러 저장소가 같은 문제를 반복할 때 조직 ruleset, reusable workflow, audit,
   metrics, cross-repository discovery를 추가한다.

## 2. 현재 상태

### 확인된 사실

- 저장소는 private이며 `master`와 `develop` 보호 규칙 및 repository ruleset이 없다.
- 현재 플랜에서는 private 저장소 protection API가 활성화되지 않는다.
- CI는 Ubuntu, macOS, Windows와 지원 Python 조합에서 동작한다.
- 첫 PR은 모든 CI를 통과했지만 독립 review 없이 병합됐다.
- CODEOWNERS와 PR template이 없다.
- 코어는 locale, ID, lifecycle, schema, relationship, index, CHECK의 repository
  state를 결정론적으로 검증한다.
- 중앙 서비스, 사용자 계정, 조직 RBAC, audit export, telemetry는 없다.

### 객관적 판단

현재 상태는 “엔터프라이즈 준비 완료”가 아니라 **강한 로컬 코어를 가진 팀 도입
전 단계**다. 중앙 서버와 telemetry가 없는 것은 개인 정보·오프라인 사용 측면에서는
장점이지만, 조직은 누가 어떤 결정을 승인했고 정책 예외가 언제 만료되는지를 별도
시스템 없이 집계할 수 없다.

## 3. 유지해야 할 설계 원칙

### Deterministic Core, Agentic Edge

코어가 소유해야 하는 범위는 ID, lifecycle transition, schema, relationship
invariant, index, filename, locale catalog, CHECK 규칙이다. Agent는 언어 추론, 초안,
근거 추출, 관련 ADR 탐색, semantic slug 제안을 도울 수 있다. Agent 출력은 저장소에
반영되기 전에 항상 코어의 검증 경계를 통과해야 한다.

### Human-localized, machine-stable

사람이 읽는 제목·본문·prompt는 팀 언어를 따르되 ID, status, relationship, locale
code, 파일명 계약은 기계적으로 안정적이어야 한다. 코어가 제목을 번역해 semantic
slug를 만들어서는 안 된다.

### No false governance confidence

자동화할 수 없는 판단은 실패나 성공으로 꾸미지 않고 `UNVERIFIABLE`로 표시한다.
CI 통과는 구조화된 정책의 증거일 뿐, 결정의 사업적 타당성이나 조직 합의의 증거가
아니다.

## 4. 공개 저장소 전환 Gate

사용자가 계획한 public 전환 직후 다음 repository ruleset을 적용하고 API로 실제
상태를 재조회한다.

| 대상 | 권장 통제 | 도입 이유 |
| --- | --- | --- |
| `master` | PR 필수, required CI, conversation resolution, force-push/deletion 차단 | 릴리스 이력과 tag 기준점 보호 |
| `develop` | PR 필수, required CI, conversation resolution, force-push/deletion 차단 | 통합 브랜치의 회귀 차단 |
| `v*` tag | 생성/수정/삭제 권한 제한 | 공개 릴리스 provenance 보호 |
| 예외 | 최소 인원 bypass, 사유 기록, 정기 검토 | 운영 복구 수단과 감사 가능성의 균형 |

GitHub ruleset은 required pull request, status check, code-owner review,
conversation resolution, signed commit, force-push와 deletion 제한을 제공한다.
실제 조합은 maintainer 수와 자동화 계정 요구에 맞춰 최소 권한으로 정한다.
([GitHub ruleset rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets))

public 전환과 동시에 추가할 최소 파일은 다음과 같다.

- PR template: ADR 영향 여부, 관련 ADR ID, CHECK 결과, 문서 변경, 예외 사유를 묻는다.
- `CONTRIBUTING.md`: Git Flow, required checks, ADR lifecycle, release 절차를 설명한다.
- `SECURITY.md`: 취약점의 비공개 신고 경로와 지원 범위를 밝힌다.
- CODEOWNERS: 실제로 독립 승인할 수 있는 qualified maintainer가 2명 이상일 때
  활성화한다. 한 사람만 있는 상태에서 필수 code-owner review를 켜면 운영을 막거나
  형식적인 self-review만 만들 수 있다.

## 5. 팀 단위 운영 모델

AWS는 ADR에 단일 owner를 두고 Proposed 상태에서 이해관계자 peer review를 거친 뒤
Accepted로 전환하며, 승인된 기록은 새 ADR로 supersede할 것을 권고한다. Microsoft도
status, considered options, tradeoffs, consequences를 포함하는 append-only 기록을
권장한다.
([AWS ADR process](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html),
[Microsoft ADR guidance](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record))

이를 Toolkit에 적용한 권장 역할은 다음과 같다.

| 역할 | 책임 |
| --- | --- |
| Decision owner | 맥락·선택지·근거·consequence를 완성하고 review를 요청 |
| Required reviewer | 영역 전문성과 영향 범위를 확인하고 독립 승인 |
| Repository maintainer | lifecycle invariant, CI, merge, release 통제 유지 |
| Exception owner | 정책 예외의 사유, 범위, 만료일, 후속 조치 소유 |

운영 절차는 Proposed → review → Accepted → implementation evidence → periodic review
순으로 둔다. Accepted ADR의 사실 오류를 몰래 고치지 않고, 결정 변경은 새 ADR과
supersession으로 남긴다. 긴급 예외는 owner와 만료일이 없는 영구 bypass가 되지 않게
한다.

## 6. 조직 단위 확장

### 6.1 중앙 정책 배포

여러 저장소에서 같은 보호 규칙이 반복될 때 organization ruleset을 사용한다.
GitHub 조직 ruleset은 repository targeting, enforcement status, bypass actor를 중앙에서
관리할 수 있다. GitHub Actions의 reusable workflow는 공통 검증 로직을 한 곳에 두고
여러 workflow에서 호출할 수 있다.
([GitHub organization rulesets](https://docs.github.com/en/organizations/managing-organization-settings/managing-rulesets-for-repositories-in-your-organization),
[GitHub reusable workflows](https://docs.github.com/en/actions/how-tos/reuse-automations/share-with-your-organization))

권장 구성은 다음과 같다.

- 조직 ruleset: protected branch/tag와 bypass 정책
- reusable workflow: validate, index-drift, CHECK, schema/config parity
- repository-local config: 팀 locale과 ADR directory처럼 저장소가 소유할 값
- 중앙 taxonomy: domain, risk, regulatory classification처럼 조직 간 집계할 값
- exception registry: 규칙, owner, 승인자, scope, 생성일, 만료일, 해소 상태

중앙 정책은 저장소의 모든 결정을 대신하지 않는다. 조직 공통 invariant만 중앙화하고,
제품 맥락과 결정 본문은 해당 저장소가 소유해야 변경 속도와 책임 소재가 유지된다.

### 6.2 RBAC와 감사

최소 권한 역할을 maintainer, decision owner, reviewer, auditor로 분리하고, bot에는
검증에 필요한 read/check 권한만 준다. bypass는 소수 역할에 한정하고 사용 이벤트를
감사한다. GitHub audit log는 조직의 actor, action, 대상, 시각을 조회·내보낼 수 있어
ruleset 변경과 bypass 검토의 근거가 된다.
([GitHub audit log](https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-security-settings-for-your-organization/reviewing-the-audit-log-for-your-organization))

Toolkit 자체에 계정 시스템을 서둘러 넣기보다 GitHub의 인증·권한·감사를 활용하고,
제품은 ADR 상태와 검증 결과를 기계 판독 가능한 산출물로 제공하는 편이 단순하고
신뢰 경계가 명확하다.

## 7. 측정 가능한 도입 지표

지표는 감시나 생산성 순위가 아니라 workflow 병목과 정책 부채를 찾는 용도로만
사용한다.

| 지표 | 정의 | 해석 시 주의점 |
| --- | --- | --- |
| Decision lead time | ADR 최초 Proposed 시각부터 Accepted/Rejected 시각까지의 중앙값 | 짧다고 결정 품질이 자동으로 높지 않음 |
| Review latency | review 요청부터 첫 qualified review까지의 중앙값 | 시간대·휴가·팀 규모를 함께 봐야 함 |
| Supersession rate | 기간 내 Accepted ADR 중 superseded된 비율 | 높은 값은 학습일 수도, 불안정일 수도 있음 |
| Unresolved violations | mainline에서 열린 `VIOLATED` 결과 수와 지속 일수 | rule coverage 밖의 문제는 포함하지 않음 |
| Exception age | 만료되지 않은 예외의 생성 후 경과 일수와 만료 초과 수 | 예외 개수보다 owner·만료·해소가 중요함 |
| Stale review coverage | review 주기를 넘긴 active ADR / review 대상 active ADR | 모든 ADR에 동일 주기를 강제하지 않음 |

성숙도 수준 5는 이 지표를 수집한다는 사실만으로 달성되지 않는다. 정의가 버전 관리되고,
예외와 audit evidence를 재현할 수 있으며, 지표가 실제 운영 개선으로 연결돼야 한다.

## 8. 서비스 개선 우선순위

### 다음 구현 후보

1. ~~ADR directory 로딩을 공통 iterator로 통합해~~ **완료 (2026-08-30).**
   `core.adr_directory.iter_adr_files`로 validate/index/related/CHECK를 통합했고
   각 명령의 warning 의미는 그대로 유지했다.
2. public 전환 시 PR template과 CONTRIBUTING/SECURITY 문서를 만들고 ruleset 적용을
   자동 검증한다. **저장소가 아직 private이라 시작 조건이 충족되지 않았다.**
3. ~~CHECK 결과를 `VERIFIED`, `VIOLATED`, `NOT_APPLICABLE`, `UNVERIFIABLE`의
   안정된 machine-readable contract로 승격한다.~~ **완료 (2026-08-30).** 모든
   finding이 기존 `kind` 값과 별개로 `confidence` 필드를 직접 갖는다
   (`related→VERIFIED`, `verified_violation→VIOLATED`,
   `review_required`/`no_applicable_constraint→UNVERIFIABLE`; 관련 ADR/finding
   자체가 없으면 `NOT_APPLICABLE`, 이는 빈 `findings` 배열로 표현되고 별도
   finding을 만들지 않는다). README, SKILL.md, `conflict-rules.md`, quickstart
   예제 출력을 모두 갱신했다.
4. 예외에 owner, reason, scope, expiry를 요구하는 작은 schema부터 시작한다.
   **아직 시작 전.** 현재 `register_exception`은 CHECK finding의 해결 옵션
   문자열로만 존재하고, 실제 저장·검증하는 schema나 명령은 없다.
5. 두 개 이상의 저장소가 같은 운영 문제를 보일 때 reusable workflow와 조직
   taxonomy를 설계한다. **시작 조건(2개 이상 저장소) 미충족.**

### 지금 구현하지 않을 것

- 중앙 포털, 벡터 검색, GitHub App은 flat-directory와 GitHub Action의 실제 한계가
  측정되기 전에는 비용이 더 크다.
- 자동 번역과 자동 semantic slug 확정은 결정성을 약화하므로 코어에 넣지 않는다.
- 독립 reviewer가 없는 현재 저장소에서 mandatory CODEOWNERS 승인을 형식적으로
  켜지 않는다.
- 모든 산문 ADR을 자동 검증하려 하지 않는다. 검증할 수 없는 판단은 사람의 review
  대상으로 남긴다.

## 9. 단계별 완료 조건

| 단계 | 완료 조건 |
| --- | --- |
| v0.2.0 | P0 전체 통과, 최종 PR CI, 승인된 version bump와 release 절차 |
| Public | `master`/`develop`/`v*` ruleset API 검증, PR template, CONTRIBUTING, SECURITY |
| Team | 2명 이상 qualified maintainer, CODEOWNERS 독립 승인, 예외 owner/expiry |
| Enterprise | 조직 ruleset·reusable workflow, audit export, taxonomy, 정의된 adoption metrics |
| Multi-repo | 반복된 탐색 실패와 운영 요구를 근거로 registry/portal 도입 |

이 순서라면 v0.2.0의 핵심 메시지인 “AI는 ADR 작성을 도울 수 있지만 architecture
governance의 진실은 결정론적 검증이 보장한다”를 유지하면서도, 실제 사용 증거가
생길 때만 운영 복잡도를 추가할 수 있다.
