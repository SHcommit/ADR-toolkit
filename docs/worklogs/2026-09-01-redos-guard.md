# CHECK의 사용자 정의 regex에 대한 ReDoS 방어 (런타임 + 정적, 2단계)

## 날짜

2026-09-01

## 문제 상황

`constraints:` 블록의 `forbidden_import`/`dependency_forbidden` 규칙은
작성자가 임의의 정규식(`pattern` 필드)을 직접 써서 diff의 추가된 줄에
매칭시킨다(`rules/conflict.py::_content_pattern`). 이 정규식은 ADR
작성자가 통제하므로, 실수든 악의든 `(a+)+$`류의 catastrophic
backtracking 패턴이 들어가면 `re.search()`가 사실상 무한정 멈추지
않는다 — CHECK 전체가 그 한 줄에서 행(hang)될 수 있었다.

## 기존 구조나 방식의 한계

- `_content_pattern`이 `re.compile(pattern).search(line)`을 아무 보호
  장치 없이 호출했다.
- 이 CLI는 CI 파이프라인(`harness-parity`, PR 체크 등)에서 자동 실행되는
  경우가 많아, 한 번 hang이 나면 사람이 알아채기 전까지 CI 러너가
  타임아웃될 때까지 계속 잡아먹는다.
- Python 표준 라이브러리에는 정규식 실행 타임아웃 기능이 없다 —
  `signal.alarm`/`setitimer`로 직접 인터럽트를 걸어야 하는데, 이는
  **POSIX 전용**(Windows는 `SIGALRM` 자체가 없음)이라 단일 메커니즘으로
  모든 CI 플랫폼(ubuntu/macos/windows)을 커버할 수 없었다.

## 관련 코드 맥락

- `skills/adr-toolkit/scripts/rules/conflict.py::_content_pattern()` —
  diff의 각 추가된 줄에 대해 규칙의 모든 `pattern`을 매칭 시도하는
  실제 실행 지점.
- `skills/adr-toolkit/scripts/commands/check.py` — 기존에 이미
  `except re.error`로 정규식 컴파일 오류를 잡아 `BAD_CONSTRAINTS`
  경고로 격하시키는 처리 경로가 있었음 — 이 기존 경로를 재사용할 수
  있는지가 설계의 핵심이었다.
- `skills/adr-toolkit/scripts/core/constraints.py::_parse_rules()` —
  `constraints:` YAML 블록을 파싱해서 규칙 리스트를 만드는 곳. 여기서
  `pattern` 값 자체를 파싱 시점에 검사할 수 있다는 게 두 번째 방어선의
  근거.

## 검토한 선택지

1. **정규식 엔진을 `re2`류 선형 시간 엔진으로 교체** — third-party
   의존성 추가가 필요해 zero-dependency 원칙과 충돌. 기각.
2. **`multiprocessing`으로 정규식 실행을 별도 프로세스에 격리하고
   `terminate()`** — 플랫폼 독립적이지만, 매 diff 라인마다 프로세스를
   새로 띄우는 오버헤드가 크고, CHECK는 원래 빠른 사전 검증 도구라는
   설계 의도와 어긋남. 기각.
3. **POSIX `SIGALRM`/`setitimer` 기반 런타임 타임아웃만 적용** —
   구현이 단순하고 기존 `except re.error` 경로에 자연스럽게 편입되지만,
   Windows에서는 완전히 무방비 상태로 남는 절반짜리 해법.
4. **런타임 타임아웃(3) + 파싱 시점 정적 휴리스틱(중첩 quantifier
   거부)을 함께 적용** — Windows/POSIX 모두 최소한의 방어선을 갖도록
   2단계로 방어. 채택.

## 판단 기준

- CI 매트릭스가 ubuntu/macos/windows 3개 플랫폼을 전부 포함하므로,
  "POSIX에서만 동작하는 방어"는 감사 관점에서 "Windows 미방어"라는
  별도의 Open Risk로 남는다 — 완전히 무시할 수 없음.
- 기존 에러 처리 경로(`except re.error`)를 재사용할 수 있으면 새
  실패 모드를 추가하지 않고 통합할 수 있다 — 최소 침습 우선.
- 정적 검사는 오탐(false positive)이 나면 정상적인 규칙 작성을 막으므로,
  가장 흔하고 확실한 패턴 모양(중첩 quantifier)만 좁게 잡는 휴리스틱이
  안전하다.

## 최종 결정

옵션 4 — `rules/conflict.py`에 런타임 SIGALRM 타임아웃 가드를
추가하고(POSIX만 유효, Windows는 가드 없이 그냥 실행), 별도로
`core/constraints.py`에 파싱 시점 정적 중첩-quantifier 거부 로직을
추가해 플랫폼 무관하게 최소 방어선을 확보했다.

## 해결 방식

1. `c0ff907` — `rules/conflict.py`에 `RegexTimeout(re.error)` 예외
   클래스와 `_guarded_search(regex, line)` 추가. `_REGEX_TIMEOUT_SECONDS
   = 0.25`로 `signal.alarm`을 걸고, 시간 초과 시 `RegexTimeout`을
   발생시킴 — `re.error`의 서브클래스이므로 `check.py`의 기존
   `except re.error` 처리가 코드 수정 없이 그대로 이를 `BAD_CONSTRAINTS`
   경고로 격하시킴. `(a+)+$`류 실제 catastrophic backtracking 패턴으로
   검증: 가드가 없으면 멈추던 것이 1초 이내에 인터럽트됨.
2. `26021a9` (Medium 패스) — `core/constraints.py`에
   `_NESTED_QUANTIFIER_RE = re.compile(r"\([^()]*" + _QUANTIFIER + r"\)"
   + _QUANTIFIER)`와 `_reject_if_redos_prone(pattern)`을 추가해
   `_parse_rules()`의 후처리 단계에서 호출. `forbidden_import`/
   `dependency_forbidden`에만 적용 — `required_path`/`forbidden_path`는
   `pattern`을 glob으로 취급(`core/globs.py` 경유)해서 애초에
   catastrophic backtracking이 발생할 수 없는 구조라, 여기에 적용하면
   오탐이 된다. 실제로 dogfooding 중인 `ADR-0011`의 constraints 블록으로
   회귀 테스트: 정상 패턴은 여전히 통과, 위험 패턴은 `re.compile()`에
   도달하기 전에 걸러짐(테스트에서 `re.compile`을 monkeypatch해서 호출
   자체가 안 됨을 확인).

## 결과

- 두 커밋 모두 실패 재현 → 가드 추가 → 통과 확인 순서로 진행.
- 남은 한계(코드 주석 및 `handoff.md`에 명시): 이 정적 휴리스틱은 가장
  흔한 "중첩 quantifier" 모양만 잡는 것이지 범용 ReDoS 탐지기가
  아니다 — `(a|a)*`류 alternation 기반 패턴은 여전히 미탐지 상태로
  남으며, Windows에서는 이 정적 검사가 유일한 방어선이다(런타임
  SIGALRM 가드가 없으므로).
- 전체 테스트 스위트 회귀 없음 확인 후 커밋.
