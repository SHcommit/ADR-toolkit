# 상관관계 ID를 포함한 구조화 JSON 에러 로깅

## 날짜

2026-09-01

## 문제 상황

`adr.py`에서 예상치 못한 예외가 발생하면 최상위 `except` 블록이 이를
잡아 JSON 에러 응답으로 stdout에 내보냈지만, 그 과정에서 스택 트레이스나
예외 컨텍스트는 어디에도 기록되지 않고 사라졌다. CI나 에이전트 하네스가
"어떤 실행에서 어떤 에러가 났는지"를 나중에 추적할 방법이 없었다.

## 기존 구조나 방식의 한계

- stdout은 이 프로젝트의 확고한 계약(ADR-0009: "always JSON contract")이라
  사람이 읽는 진단 로그를 stdout에 섞을 수 없다.
- 그렇다고 `print(traceback, file=sys.stderr)` 같은 비구조화 텍스트를
  찍으면, 여러 프로세스가 동시에 도는 CI 환경에서 어떤 stderr 줄이 어떤
  stdout JSON 응답과 짝인지 알 방법이 없다.
- 표준 `logging` 모듈을 그냥 쓰면 pytest의 capsys 캡처와 충돌하기 쉽고
  (핸들러가 이전 테스트에서 누적됨), 프로덕션에서도 매 호출마다 새
  핸들러가 쌓이는 문제가 생긴다.

## 관련 코드 맥락

- `skills/adr-toolkit/scripts/adr.py`의 최상위 `main()` 함수 —
  예외를 잡는 유일한 지점. 여기서 로거를 얻어 기록하고, 동일한
  상관관계 ID를 stdout JSON 에러 응답에도 넣어야 두 출력을 나중에
  매칭할 수 있다.
- `skills/adr-toolkit/scripts/core/telemetry.py`(신규) —
  `_JsonLogFormatter`와 `get_logger(operation, *, correlation_id=None)`를
  정의. 매 호출마다 `logger.handlers.clear()`로 핸들러를 비우고 다시
  구성하는 게 핵심 — 이래야 pytest에서 각 테스트가 독립적으로 stderr를
  캡처할 수 있고, 프로덕션에서도 핸들러가 무한정 누적되지 않는다.

## 검토한 선택지

1. **외부 로깅 서비스(Sentry, Datadog 등) 연동** — 네트워크 의존성과
   API 키 관리가 필요해 이 CLI의 "설치 즉시 동작"하는 사용 모델과
   맞지 않고, 제로 의존성 원칙과도 충돌. 기각.
2. **비구조화 stderr 텍스트 로그(`print(..., file=sys.stderr)`)** —
   구현은 가장 간단하지만, CI 로그가 뒤섞이는 환경에서 특정 실패를
   특정 stdout 응답과 연결할 방법이 없다. 기각.
3. **표준 `logging` 모듈 + JSON Lines 포맷 + 상관관계 ID를 stdout·stderr
   양쪽에 동일하게 포함** — 표준 라이브러리만 사용하고, 매 요청마다
   고유 ID를 발급해 두 출력 스트림을 연결할 수 있다. 채택.

## 판단 기준

- stdout의 JSON 전용 계약(ADR-0009)을 절대 깨지 않을 것 — 상관관계
  ID는 stdout 쪽 에러 응답에 필드 하나 추가하는 형태로만 들어간다.
- 제로 의존성 원칙 유지.
- 테스트 스위트(pytest)에서 stderr 캡처가 깨지지 않아야 함 — 이는
  구현 중 실제로 부딪힌 문제였고, 핸들러를 매번 초기화하는 방식으로
  해결했다.

## 최종 결정

`core/telemetry.py`에 JSON Lines 포맷 로거를 만들고, `adr.py`의
전역 예외 핸들러가 여기에 예외를 기록하면서 동일한 상관관계 ID를
stdout JSON 에러 응답에도 포함시킨다.

## 해결 방식

1. `11c8f4b` — `core/telemetry.get_logger(operation)`이
   `LoggerAdapter`를 반환하도록 구현. 각 로그 라인은 JSON Lines
   형식으로 `level`, `operation`, `correlation_id`, `message`,
   (예외 시) `exception_type` 필드를 담아 stderr에 출력된다.
2. `adr.py`의 예외 핸들러를 `logger = get_logger(args.operation);
   logger.exception(...)` 형태로 바꾸고, 동일한 `correlation_id`를
   stdout으로 나가는 JSON 에러 응답에도 추가 — CI 로그에서 stderr의
   특정 줄과 stdout의 특정 실패 응답을 상관관계 ID로 매칭할 수 있게 함.
3. 기본 로그 레벨은 `WARNING`(성공 시 조용함), `ADR_TOOLKIT_LOG_LEVEL`
   환경변수로 오버라이드 가능.
4. `mypy --strict` 게이트를 통과시키는 과정에서 발견된 타입 이슈(문서
   `2026-09-01-typed-contracts-mypy-strict.md` 참고)도 이 모듈에서
   함께 수정됨 — `Iterator[None]` 반환 타입, `exc_info[0]` narrowing,
   `LoggerAdapter` 제네릭 파라미터화.

## 결과

- stdout의 순수 JSON 계약은 상관관계 ID 필드 추가 외에는 변경 없음 —
  기존 소비자(에이전트, CI 스크립트)와 호환.
- pytest의 capsys 기반 테스트가 핸들러 누적 없이 안정적으로 stderr를
  캡처함을 확인.
- 같은 세션에서 이어진 TTY 전용 사람 친화적 요약 줄(`c3ed01d`,
  Medium 패스)은 이 구조화 로깅과는 별개 기능 — 그쪽은
  `sys.stderr.isatty()`일 때만 보이는 인간용 한 줄 요약이고, 이
  telemetry 로거는 항상 JSON Lines로 기록되는 기계 판독용 로그다.
