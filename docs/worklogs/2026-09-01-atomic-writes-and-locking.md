# ADR/exception/supersede 동시성 레이스 컨디션 제거

## 날짜

2026-09-01 (원 구현은 `2026-09-01` Critical 하드닝 패스)

## 문제 상황

`docs/adr-toolkit-audit-report.md`가 지적한 Critical 항목: `create`,
`exception`, `supersede` 세 커맨드 모두 "다음 순번 계산 → 파일 존재 확인
→ `Path.write_text()`로 직접 쓰기" 순서로 동작했다. 이 세 단계 사이에
원자성이 전혀 없어서, 같은 저장소에 대해 두 프로세스가 동시에
`adr.py create`를 호출하면 둘 다 같은 다음 번호(예: `ADR-0012`)를
계산해서 서로의 파일을 덮어쓸 수 있었다.

## 기존 구조나 방식의 한계

- ID 할당에 락이나 원자적 연산이 전혀 없어, "다음 번호 읽기"와 "그
  번호로 쓰기" 사이에 임의의 다른 프로세스가 끼어들 수 있었다.
- `Path.write_text()`는 원자적이지 않다 — 쓰기 도중 프로세스가
  죽으면(OOM kill, SIGKILL, 정전) 파일이 반쯤 쓰인 상태로 남을 수 있다.
- 실제로 재현해서 확인함: 수정 전 코드로 20개 concurrent `create` 호출을
  실행하자 고유 ADR ID가 13개만 생성됐다(`49ede49` 커밋 메시지에 기록).
  `exception`도 동일한 방식으로 재현: 20개 중 18개만 고유 ID(`68bbd98`).

## 관련 코드 맥락

- `skills/adr-toolkit/scripts/commands/create.py`의 `run()` — 다음 ID
  계산 후 `_build_frontmatter()`로 프런트매터를 만들고 파일에 쓰는
  부분이 원래 아무 보호 없이 실행됐다.
- `skills/adr-toolkit/scripts/commands/exception.py`의 `run()` — 동일한
  패턴이지만, `SCHEMA_ERROR`(잘못된 draft) 시에는 애초에 아무 파일도
  만들면 안 된다는 기존 테스트 제약이 있었다.
- `skills/adr-toolkit/scripts/commands/supersede.py`의 `run()` — 구
  ADR과 신규 ADR 두 파일을 순서대로 갱신하는데, 첫 파일 쓰기 후 둘째
  파일 쓰기가 실패하면 롤백을 시도하는 기존 로직이 이미 있었다.

## 검토한 선택지

1. **파일 시스템 락 없이 재시도/충돌 감지만 추가** — 쓰기 후 "내가 쓴
   파일이 맞는지" 재확인하는 낙관적 동시성 제어. 구현이 복잡해지고
   재시도 로직 자체에 새로운 엣지 케이스가 생김. 기각.
2. **SQLite 등 외부 상태 저장소로 ID 카운터 이전** — 이 프로젝트의
   "third-party 런타임 의존성 0개" 원칙(zero-dependency 아키텍처
   가치)과 정면충돌. 기각.
3. **크로스 플랫폼 파일 락(`fcntl`/`msvcrt`) + 임시파일→`os.replace`
   원자적 쓰기** — 표준 라이브러리만으로 두 문제(레이스 컨디션, 쓰기
   도중 크래시)를 동시에 해결. 채택.

## 판단 기준

- 이 프로젝트는 third-party 런타임 의존성이 전혀 없는 것이 의도된
  아키텍처 가치(감사 세션 내내 여러 번 확인됨) — 표준 라이브러리만으로
  해결 가능한지가 최우선 기준.
- Windows/macOS/Linux 3.9~3.12 CI 매트릭스를 그대로 지원해야 하므로,
  POSIX 전용 API(`fcntl`)만으로는 부족하고 플랫폼 분기가 필요.
- 기존 dry-run 테스트("dry-run은 아무것도 생성하면 안 된다")를 깨지
  않아야 함.

## 최종 결정

`core/atomic_io.py`에 `atomic_write_text()`(임시파일 + `os.fsync` +
`os.replace`)와 `adr_directory_lock()`(POSIX `fcntl.flock` / Windows
`msvcrt.locking` 컨텍스트 매니저)을 만들고, `create`/`exception`/
`supersede`의 실제 쓰기 경로를 이 두 프리미티브로 감쌌다.

## 해결 방식

1. `fc46830` — `core/atomic_io.py` 신설. 아직 어떤 커맨드에도 연결하지
   않은 순수 프리미티브 단계로 먼저 커밋(리뷰 단위를 작게 유지).
2. `49ede49` — `create.py`: ID 할당 + 존재 확인 + 쓰기 전체를
   `adr_directory_lock()`으로 감싸고 `write_text`를
   `atomic_write_text`로 교체. **dry-run 경로는 락 밖에 완전히 남겨둠**
   — dry-run이 `adr_dir`나 락 파일을 생성하면 기존 테스트가 깨지고,
   dry-run은 아무것도 영속화하지 않으므로 거기서 레이스가 나도 무해함.
3. `68bbd98` — `exception.py`도 같은 패턴이되 한 가지 추가 보정: 스키마
   검증은 **디스크를 건드리기 전에** preview ID로 미리 수행. 유효성
   검증 결과가 실제로 어떤 순번을 받는지와 무관하기 때문에, 이렇게
   해야 "SCHEMA_ERROR 시 exceptions_dir조차 만들면 안 된다"는 기존
   테스트와 "dry-run은 아무것도 안 만든다"는 테스트를 모두 만족시킴.
   락은 최종 ID 할당 + 원자적 쓰기 구간만 감쌈.
4. `cec7215` — `supersede.py`: 두 파일 갱신 전체를 락으로 감싸고, 두
   번의 `write_text` 호출과 롤백 쓰기까지 전부
   `atomic_write_text`로 교체. 기존 테스트 2개
   (`test_supersede_rolls_back_old_file_when_new_file_write_fails`,
   `test_supersede_double_write_failure_reports_inconsistent_state_not_silent`)가
   `Path.write_text`를 직접 monkeypatch해서 쓰기 실패를 흉내내고
   있었는데, 그 시드(seam)가 사라져서
   `supersede.atomic_io.atomic_write_text`로 재타게팅 — 테스트의 원래
   의도와 검증 내용은 그대로 유지.

## 결과

- 재현 테스트로 수정 전 실패(레이스 발생)를 먼저 확인한 뒤 수정 →
  TDD 순서를 지킴.
- OS 레벨 검증(fork + SIGKILL)까지 별도로 수행해, 쓰기 도중 프로세스가
  강제 종료돼도 ADR 파일이 반쯤 쓰인 상태로 남지 않음을 확인
  (High-priority 패스, `9708bb2`).
- 알려진 남은 한계 (`handoff.md`에 기록): `supersede`의 개별 파일 쓰기는
  각각 원자적이지만, 두 파일 쓰기 "사이"에 프로세스가 죽으면 두 파일
  쌍 전체의 일관성(진짜 2-phase commit)까지는 보장하지 않음 — 의도적으로
  범위 밖으로 둔 것.
- 성공적인 `create`/`exception`/`supersede` 호출마다 `.adr-toolkit.lock`
  (0바이트 dotfile)이 `docs/decisions/`, `docs/decisions/exceptions/`
  안에 영구히 남는다 — 크로스 프로세스 뮤텍스로서 의도된 동작이며
  `*.md`/`*.json` glob과 충돌하지 않음.
