# ADR Toolkit v0.2.0 준비도 보고서

작성일: 2026-08-30

평가 대상: `develop-2` 브랜치

릴리스 성격: 하위 호환을 유지하는 다국어 기능 추가이므로 patch가 아닌 minor release

## 1. 결론

v0.2.0의 제품 구현 범위는 로컬 검증 기준으로 릴리스 준비가 끝났다. 저장소 기본
언어 설정, 8개 언어의 결정론적 문서 생성, 비 ASCII 제목과 이식 가능한 파일명,
런타임과 JSON Schema의 locale 일치, 기존 ADR 품질 보강, CHECK의 false-clean 결함
수정이 모두 테스트로 확인됐다.

다만 **현재 판정은 `조건부 GO`**다. `develop-2`의 최종 변경이 PR의 필수 CI를
통과하고, 소유자가 v0.2.0 버전 변경을 승인한 뒤 release 브랜치를 통해
`master`에 병합하기 전에는 태그를 만들면 안 된다. 이는 기능 결함 때문이 아니라
저장소가 채택한 릴리스 절차의 남은 통제 단계다.

## 2. 평가 방법

### 2.1 성숙도 기준

| 수준 | 재현 가능한 의미 |
| --- | --- |
| 1 | 프로토타입 또는 수동 절차만 존재한다. |
| 2 | 기능은 존재하지만 중요한 정확성·운영 공백이 남아 있다. |
| 3 | 개인 또는 소규모 팀이 테스트와 문서에 따라 반복 사용할 수 있다. |
| 4 | CI와 저장소 거버넌스로 같은 보장을 반복 검증하고 강제할 수 있다. |
| 5 | 조직 단위 정책, 권한, 감사, 예외, 측정 체계가 운영된다. |

점수는 정성적 소수점 대신 충족한 증거로 결정했다. 로컬 테스트가 충분하더라도
현재 작업 브랜치의 PR CI와 보호 규칙으로 강제되지 않으면 수준 4로 올리지 않았다.

### 2.2 근거 구분

- **저장소 사실**: 코드, 테스트, 명령 출력, GitHub API에서 직접 확인한 상태다.
- **외부 관행**: AWS, Microsoft, GitHub의 공식 문서에서 확인한 권고나 기능이다.
- **평가·추론**: 위 근거로부터 도출한 현재 수준과 권고이며 제품 사실과 구분한다.

## 3. 객관적 기준선

| 영역 | 현재 수준 | 측정 신호 | 수준을 올리기 위한 조건 |
| --- | ---: | --- | --- |
| 결정론적 코어 | 3 | ID, lifecycle, schema, 관계, index, config를 테스트하며 전체 274개 테스트 통과 | 최종 PR CI를 필수 검사로 강제 |
| ADR 내용·lifecycle | 3 | ADR 6개 유효, 소유자·근거·locale 보강, ADR-0003과 ADR-0006 양방향 supersession 검증 | 독립 리뷰어와 CODEOWNERS 승인 강제 |
| 국제화 | 3 | 8개 locale catalog key parity와 INIT → CREATE → VALIDATE → INDEX E2E 통과 | PR CI 및 원어민 용어 검수 체계 |
| CHECK 신뢰성 | 3 | git 증거 수집 실패 시 fail-closed, rename 양 경로, ignore 및 diff-mode 회귀 테스트 | 실제 저장소 fixture 확대와 필수 CI 적용 |
| GitHub 거버넌스 | 2 | CI 5개 조합은 운영되지만 `master`/`develop` 보호와 ruleset, 필수 리뷰가 없음 | 공개 전환 후 ruleset을 API로 검증 |
| 엔터프라이즈 확장성 | 1 | 방향과 경계만 문서화됐고 조직 정책·감사·측정 구현은 없음 | 별도 도입 단계와 운영 데이터 필요 |

국제화와 CHECK가 수준 3인 것은 기능 부족을 뜻하지 않는다. 기능 계약은 P0를
충족하지만, 현재 브랜치에서 조직적 강제까지 확인하지 않았기 때문이다.

## 4. v0.2.0 구현 검증

### 4.1 결정론적 다국어 생성

**저장소 사실**

- 정식 locale은 `en`, `ko`, `ja`, `zh`, `fr`, `es`, `de`, `pt-BR` 8개다.
- `.adr-toolkit.json`이 저장소 기본 locale을 보유하며, 명령의 결정 순서는
  `CLI --locale` → 입력 draft의 locale → 저장소 기본값 → `en`이다.
- Agent는 사용자 명시 요청 → 요청 언어 → 저장소 기본값 → `en` 순으로 locale을
  정하되, 결과는 동일한 결정론적 validator를 통과해야 한다.
- INIT, interactive CREATE, template, prompt, INDEX는 같은 catalog loader를
  사용한다. input CREATE는 승인된 사용자 본문을 번역·재렌더링하지 않고 선택된
  locale metadata를 기록한다. 모든 catalog는 영어 key 집합과 정확히 일치한다.
- config의 알 수 없는 버전·키·locale은 묵시적으로 무시되지 않고 실패한다.
- locale 없는 기존 ADR은 계속 유효하며, locale이 있으면 런타임 validator와
  `adr.schema.json`이 같은 8개 값만 허용한다.

### 4.2 파일명 정책

사용자의 Unicode 제목과 본문은 보존한다. 코어는 의미 번역이나 음역을 하지 않는다.
승인된 ASCII slug가 있으면 이를 검증해 사용하고, 안전한 ASCII slug를 만들 수
없으면 `decision`으로 되돌아간다. ID가 앞에 붙으므로 충돌 없이
`0006-decision.md` 같은 이식 가능한 이름을 만든다.

Agent는 `separate-payment-system` 같은 의미 있는 slug를 제안할 수 있지만, 사용자의
확인과 코어의 ASCII 규칙 검증을 모두 거쳐야 한다. 이 경계가
**Deterministic Core / Agentic Edge** 원칙을 실제 동작으로 만든다.

### 4.3 Dogfooding ADR 품질

**수정한 사실**

- 기존 ADR에 승인된 decision maker와 `locale: en`을 기록했다.
- 사후 작성 ADR에는 확인된 증거, 추론한 근거, 알 수 없는 내용을 분리했다.
- ADR-0004를 Full MADR 구조로 보강하고 affected paths와 confirmation을 구체화했다.
- MVP의 index-only 국제화 결정인 ADR-0003을 유지한 채, 저장소 기본 locale과
  다국어 생성을 채택한 ADR-0006이 이를 양방향으로 supersede하도록 lifecycle
  명령으로 변경했다.
- 생성된 ADR index를 두 번 생성해 동일한 해시가 유지되는 것을 확인했다.

AWS는 중요한 결정에 context, decision, consequences와 명확한 소유자를 두고,
승인된 ADR은 직접 고치는 대신 새 ADR로 대체할 것을 권고한다. Microsoft 역시 ADR을
append-only 기록으로 취급하고 status와 supersession을 명시하도록 설명한다.
현재 lifecycle 보강은 이 외부 관행과 일치한다.
([AWS ADR process](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html),
[Microsoft ADR guidance](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record))

### 4.4 CHECK의 검증 한계

CHECK는 검증할 수 없는 정책까지 증명했다고 주장하지 않는다.

| 결과 의미 | 해석 |
| --- | --- |
| `VERIFIED` | 구조화된 규칙과 git 증거로 정책 준수를 증명할 수 있다. |
| `VIOLATED` | 구조화된 규칙과 증거가 위반을 확인한다. |
| `NOT_APPLICABLE` | 현재 변경에 적용되는 구조화된 규칙이 없다. |
| `UNVERIFIABLE` | 산문·조직적 근거처럼 현재 rule vocabulary로 증명할 수 없다. |

구현은 두 diff 호출과 tracked/untracked 파일 수집 실패를 모두 오류로 처리하고,
rename의 이전·새 경로와 Unicode 경로를 보존한다. 파일 존재 판단은 Git의
tracked/untracked/ignore 및 working-tree 삭제 의미를 따르며 서로 충돌하는 diff
mode를 거부한다. schema-invalid ADR은 묵시적으로 제외하지 않고 warning으로
노출한다. `--root`를 쓸 때 상대 `--dir`은 caller CWD가 아니라 repository root에서
일관되게 해석한다. 따라서 현재까지 재현된 “증거를 못 읽었는데 clean으로 보이는”
경로는 닫혔다. 이 분류는 앞으로의 결과 모델이며, 현재 CLI의 세부 finding 이름과
일대일로 같다는 뜻은 아니다.

## 5. Release Gates

### P0 — Release Blocking

| Gate | 결과 | 증거 |
| --- | --- | --- |
| 비 ASCII 제목 생성 | PASS | 한국어 제목·본문 생성과 fallback/semantic slug 회귀 테스트 |
| locale catalog/loader 결정성 | PASS | 8개 catalog key parity 및 config 오류 테스트 |
| INIT / CREATE / INDEX의 정식 locale 지원 | PASS | 8-locale input E2E와 8-locale interactive prompt/render matrix |
| 런타임 validator / JSON Schema 일치 | PASS | locale parity 테스트, 기존 locale-less ADR 호환 |
| 기존 ADR의 RECORD 품질 계약 | PASS | 저장소 ADR 품질 테스트 4개 및 6개 ADR validation |
| CHECK false-confidence 정확성 | PASS | subprocess, rename, Unicode, deletion, schema warning, ignore, path, diff-mode 회귀 테스트 |
| 전체 테스트 | PASS | `python3 -m pytest -q` → `290 passed`, exit 0 |
| 버전 파일 드리프트 | PASS | `python3 scripts/sync_version.py --check` → exit 0 |

### P1 — Strongly Recommended

| 항목 | 결과 |
| --- | --- |
| 한국어 준비도 보고서 | PASS — 본 문서 |
| README 다국어 사용 예시 | PASS |
| 비라틴 quickstart | PASS — 한국어 기본 locale, semantic slug, 한국어 index의 실제 실행 결과 포함 |
| Dogfooding ADR 품질 개선 | PASS |
| work-tracking 문서 정합성 | PASS — 완료 항목은 `improvements.md`의 Done으로 이동 |

### P2 — Post Release

공개 저장소 ruleset, CODEOWNERS, 조직 ruleset, enterprise 도입 지표,
cross-repository discovery는 v0.2.0을 막지 않는다. 구체적인 단계와 통제는
`docs/enterprise-adoption.md`에서 분리한다.

## 6. 실제 GitHub 상태와 릴리스 판정

**2026-08-30에 확인한 저장소 사실**

- 저장소는 private이고 기본 브랜치는 `master`다.
- `master`, `develop` branch protection과 repository ruleset이 없다.
- 현재 private 플랜에서 protection/ruleset API는 업그레이드 또는 public 전환을
  요구하며 403을 반환한다.
- 첫 PR은 Ubuntu/macOS/Windows와 Python 3.9/3.12의 5개 CI 검사를 모두 통과했지만,
  별도 review 없이 병합됐다.
- CODEOWNERS와 PR template은 아직 없다.

**평가**

기능 구현에 대한 P0는 통과했다. 그러나 최종 변경이 원격 PR CI를 통과하지 않았고
manifest 버전은 승인 없이 바꾸지 않았으므로, 지금 즉시 `v0.2.0` 태그를 만드는
판정은 `NO-GO`다. 다음 세 조건을 만족하면 별도 설계 변경 없이 `GO`로 전환할 수
있다.

1. `develop-2` 변경을 PR로 올려 필수 CI가 모두 통과한다.
2. 소유자가 v0.2.0 version bump를 승인하고 `scripts/sync_version.py`로 전파한다.
3. release 브랜치를 `master`와 `develop`에 정책대로 반영한 뒤 tag가 `master`의
   해당 커밋을 가리키는지 확인한다.

공개 전환 후에는 GitHub ruleset으로 PR, required status checks, conversation
resolution, force-push/deletion 차단을 강제하고 API로 실제 적용을 확인해야 한다.
GitHub 공식 문서상 ruleset은 이 통제들을 제공하며 공개 저장소에서도 사용할 수
있다.
([GitHub ruleset rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets))

## 7. 남은 위험

- 8개 언어의 구조와 결정성은 검증했지만 전문 용어의 자연스러움은 각 언어
  사용자의 검수를 대체하지 않는다.
- CHECK는 구조화된 경로·dependency 규칙만 증명한다. 사업적 타당성, 조직 효과,
  산문의 진실성은 `UNVERIFIABLE`로 남기는 것이 올바르다.
- 현재 저장소에서는 독립 리뷰와 브랜치 통제가 강제되지 않는다. public 전환 전에는
  운영 절차가 사람의 준수에 의존한다.
- v0.2.0 버전 변경, release branch, push, tag는 이번 구현 범위에 포함되지 않았다.
