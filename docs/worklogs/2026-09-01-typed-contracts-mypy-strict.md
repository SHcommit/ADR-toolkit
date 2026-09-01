# 타입드 결과 계약(`core/contracts.py`)과 범위 한정 `mypy --strict` 게이트

## 날짜

2026-09-01

## 문제 상황

`adr.py`의 모든 커맨드는 "stdout은 항상 순수 JSON"이라는 계약(ADR-0009)을
따르지만, 그 JSON이 실제로 어떤 키를 가지는지는 각 커맨드의 `run()`
함수 본문을 읽어야만 알 수 있었다 — 타입 시스템 차원에서 보장되는
스키마가 전혀 없었다. 감사 보고서는 이를 "출력 계약이 코드에만 존재하고
타입으로 고정되지 않음" 문제로 지적했다.

## 기존 구조나 방식의 한계

- 16개 커맨드 모두 `dict`를 리턴하며, 필드 이름 오타나 필드 누락이
  런타임에만(혹은 소비하는 쪽 에이전트/스크립트에서만) 드러남.
- `jsonschema` 같은 런타임 스키마 검증 라이브러리를 쓰면 즉시 해결될
  것처럼 보이지만, 이 프로젝트의 zero-dependency 원칙과 충돌한다.
- `argparse.Namespace`로 넘어오는 커맨드 인자(`args`)는 동적 속성
  접근이라 `TypedDict`로 감싸기 어렵다 — 인자 쪽까지 완전히 타입화하려면
  `Protocol` 기반의 더 큰 리팩터링이 필요해서, 이번 패스에서는 "출력
  결과 타입"만 범위로 잡았다.

## 관련 코드 맥락

- `skills/adr-toolkit/scripts/core/atomic_io.py`,
  `core/telemetry.py` — 이번 세션에서 새로 만든, 처음부터 완전히
  타입 주석이 붙은 두 모듈. `mypy --strict` 게이트의 첫 적용 대상.
- `skills/adr-toolkit/scripts/commands/create.py`의 `run()` 리턴문 —
  `CreateResult` TypedDict의 필드 목록을 정할 때 실제 리턴 딕셔너리를
  읽고 역으로 타입을 뽑아냄(추측이 아니라 코드에서 도출).
- `.github/workflows/test.yml`의 `type-check` job — `mypy --strict`를
  세 모듈(`atomic_io`, `telemetry`, `contracts`)에만 한정해서 실행.

## 검토한 선택지

1. **`jsonschema` 도입 + JSON Schema로 런타임 검증** — 스펙 표준이라는
   장점은 있지만 제로 의존성 원칙 위반. 기각.
2. **`dataclasses`로 결과 객체를 감싸고 `asdict()`로 직렬화** — 런타임
   오버헤드와 기존 dict 기반 코드 전체(16개 커맨드, 관련 테스트 전부)를
   바꿔야 하는 큰 리팩터링이 필요해 이번 감사 대응 범위에 비해 과함.
   기각.
3. **`TypedDict` + `mypy --strict`를 다 타입화된 모듈에만 우선
   적용** — 런타임 동작을 전혀 바꾸지 않고(TypedDict는 런타임에 아무
   효과가 없음) 정적 분석만으로 계약을 문서화·검증. 채택.

## 판단 기준

- 런타임 동작을 바꾸지 않으면서 "출력 계약을 코드로 고정"하는 최소
  침습적 방법이 우선.
- 이미 확인된 제로 의존성 제약을 다시 어기지 않을 것.
- `argparse.Namespace` 타입화라는 더 큰 리팩터링까지 한 패스에 묶으면
  범위가 과도하게 커지므로, "출력 타입만" 먼저 고정하고 인자 타입화는
  모듈 docstring에 명시적으로 향후 과제로 남긴다.

## 최종 결정

`core/contracts.py`에 커맨드별 결과 `TypedDict`를 정의하고,
`mypy --strict` CI 게이트를 새로 만들되 이미 완전히 타입 주석이 붙은
핵심 모듈에만 적용한다. 명령어 인자(`argparse.Namespace`) 타입화는
범위 밖으로 명시적으로 남긴다.

## 해결 방식

1. `305c836` — `core/contracts.py` 신설:
   `CommandError`/`BaseResult`/`ErrorResult`/`CreateResult` 4개
   TypedDict로 시작. `type-check` CI job을 추가해 `atomic_io`,
   `telemetry`, `contracts` 세 모듈에 `mypy --strict` 적용. 이 과정에서
   실제로 발견한 3개의 진짜 mypy 오류를 수정:
   - `adr_directory_lock`의 컨텍스트 매니저 제너레이터에 `Iterator[None]`
     반환 타입 누락.
   - `record.exc_info[0]`가 `Optional[type[BaseException]]`이라 미리
     narrowing 없이 쓰면 오류 — `and record.exc_info[0] is not None`
     가드 추가.
   - `logging.LoggerAdapter`를 파라미터화하지 않은 제네릭으로 써서
     오류 — `"logging.LoggerAdapter[logging.Logger]"` 문자열 애노테이션으로
     해결.
   - (나중 커밋에서 추가 발견) TypedDict 필드에 맨 `dict`를 쓰면
     `mypy --strict`의 `type-arg` 검사에 걸림 — `Dict[str, Any]`로
     교체해야 함.
2. `1df6066` (팔로우업) — 나머지 14개 커맨드(`preflight`, `discover`,
   `init`, `index`, `related`, `significance`, `validate`, `status`,
   `supersede`, `diff`, `exception`, `graph`, `search`)까지 확장해
   2/16 → 16/16 커버리지. 각 TypedDict 필드는 실제 `run()` 리턴문을
   읽어서 결정했고(추측 금지), `status`/`supersede`의 에러 경로까지
   실제로 실행해서 대조 확인. 에러/경고/중첩 페이로드 필드는 공용
   `CommandError` 타입 대신 `Dict[str, Any]`를 쓴 경우가 있는데, 이는
   실제 에러 딕셔너리가 `file`/`id`/`ids`/`cycle` 등 `CommandError`가
   선언하지 않은 추가 필드를 갖는 커맨드가 있어서, 사실이 아닌 구조를
   타입으로 과장하지 않기 위함.

## 결과

- `mypy --strict`가 실제로 CI에 게이트로 걸려 통과 상태 유지 중.
- 남은 과제(코드 주석 및 `handoff.md`에 기록): `mypy --strict`를 16개
  커맨드 모듈 자체(현재는 결과 타입만 타입화되고 커맨드 구현부는
  미적용)까지 확장하는 건 `argparse.Namespace` 타입화 리팩터링이
  선행돼야 해서 여전히 향후 과제로 남아있다.
- 전체 테스트 스위트 회귀 없이 각 커밋 완료.
