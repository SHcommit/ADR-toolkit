# improvements.md

Concrete implementation backlog. Unscheduled product bets belong in
`project-roadmap.md`; current-session state belongs in `handoff.md`.

## Open

Backlog derived from `docs/adr-toolkit-audit-report.md`. Scope excludes
domains 1 (core/plugin architecture) and 5 (governance/FSM) — already
scored 72/80 and mostly "no action needed" in the audit. README prose is
another worktree's.

### Production Readiness Audit Findings (핵심 감점 이유 & 취약점 5선)

- [ ] **1. 설정 관리의 엄격한 한계 (`Operability` 감점 요인)**: `.adr-toolkit.json`이 `schema_version`, `locale` 외의 키(예: `adr_dir`)를 수용하지 못해, 커스텀 ADR 디렉토리를 사용하는 프로젝트에서 CLI 호출 시마다 `--dir` 플래그를 수동 입력해야 함. (개선안: `.adr-toolkit.json`에 `adr_dir` 등록 및 `ADR_DIR` / `ADR_LOCALE` 환경변수 오버라이드 지원)
- [ ] **2. 관측성 및 로그 표준화 부재 (`Observability` 감점 요인)**: 표준 `logging` 모듈을 사용하지 않고 `print()` 및 crash 시 JSON stderr만 제공하여 CLI의 `--debug`, `--verbose`, `--quiet` 로그 제어가 불가능함. (개선안: Python `logging` 레벨 및 CLI 플래그 연동)
- [ ] **3. 프로세스 비정상 종료 시 잠금/임시 파일 잔류 (`Reliability` 감점 요인)**: `atomic_io.py` 실행 중 SIGINT/SIGTERM/타임아웃 발생 시 시그널 핸들러 부재로 `.adr/lock` 및 `.tmp` 파일이 정리되지 않아 후속 프로세스가 무한 블로킹됨. (개선안: 시그널 핸들러 cleanup 및 mtime 타임아웃/`adr unlock` 도입)
- [ ] **4. 대용량 파일 파싱 시 OOM 리스크 (`Reliability` / `Performance` 감점 요인)**: 파싱 시 전체 파일 용량을 검사하지 않고 `.read_text()`로 메모리에 전체 로드하여 바이너리/대용량 파일 스캔 시 메모리가 급증함. (개선안: 10MB 상한 검사 및 스트리밍 파서 적용)
- [ ] **5. 영속 인덱스 부재로 인한 풀 스캔 성능 병목 (`Performance` / `Scalability` 감점 요인)**: CLI 실행 시마다 디스크 전체 ADR 문서를 매번 파싱하여 대규모 레포지토리에서 선형적 실행 지연 발생. (개선안: mtime 기반 인덱싱 및 단계별 `--verbose` 텔레메트리 제공)

### High (P1 - Production Readiness)

- [ ] **`.adr-toolkit.json` 및 환경 변수 설정 확장 (`Operability`)** — `skills/adr-toolkit/scripts/core/config.py`의 `ALLOWED_KEYS`가 `schema_version`, `locale`에 고정되어 커스텀 ADR 디렉토리(`adr_dir`, 예: `architecture/decisions`)를 설정 파일에 저장할 수 없고 환경 변수 오버라이드(`ADR_DIR`, `ADR_LOCALE`)가 불가능함. `.adr-toolkit.json` 및 환경 변수 경로 로딩을 지원하도록 확장 필요.
- [ ] **시그널(SIGINT/SIGTERM) 핸들링 및 스탈 잠금(.adr/lock) 자동 해제 (`Reliability`)** — `skills/adr-toolkit/scripts/core/atomic_io.py` 구동 시 시그널 핸들러가 없어 CI 타임아웃/강제 종료 시 `.adr/lock` 및 임시 `.tmp` 파일이 잔류하여 후속 CLI 실행이 영구 블로킹되는 위험. `SIGINT`/`SIGTERM` cleanup 핸들러 및 mtime/타임아웃 기반 스탈 잠금 자동 해제(또는 `adr unlock`) 메커니즘 도입.
- [ ] **CLI 표준 로그 레벨 제어 및 관측성 강화 (`Observability`)** — 단순 `print()` 및 미처리 예외 시에만 JSON stderr 출력하는 구조에서 Python 표준 `logging` 모듈로 전환하고, CLI 플래그(`--verbose`, `--debug`, `--quiet`)를 제공하여 운영/CI 환경 디버깅을 지원.

### Medium (P2 - Performance & Resilience)

- [ ] **대용량 파일 스트리밍 파싱 및 크기 상한 설정 (`Reliability`)** — `skills/adr-toolkit/scripts/commands/check.py` 등에서 `.read_text()`로 메모리에 전체 로드하는 구조 개선. 오인 스캔된 대용량/바이너리 파일 로드 시 OOM 예방을 위해 파일 크기 상한(예: 10MB) 및 스트리밍 파싱 적용.
- [ ] **`scripts/adoption_metrics.py` (41KB, 1,000줄+) 대형 모듈 리팩토링 (`Maintainability`)** — 단일 파일 내 메트릭 수집, 계산, 리포팅 로직의 높은 결합도를 해소하기 위해 서브 모듈 분리 리팩토링.
- [ ] **대규모 저장소 단계별 성능 프로파일링 및 인덱스 처리 개선 (`Performance`)** — 수백~수천 개 ADR 스캔 시 각 단계별(파일 탐색, Frontmatter 파싱, 무결성 검사) 소요 시간을 `--verbose` 모드로 출력하는 텔레메트리 기능 추가.
- [ ] **손상 상태 진단 및 복구 CLI 툴링 (`Recoverability`)** — `.adr-toolkit.json` 설정 손상이나 비정상 frontmatter 상태를 점검하고 자가 복구 가이드를 제공하는 `adr doctor` 명령 검토.

- [ ] ~~**파싱 결과 캐시**~~ — **결정: 하지 않음.** 이 CLI는 호출마다
  새 프로세스라 `functools.lru_cache`는 프로세스 간 재파싱을 전혀 줄이지
  못하고(원 문제였던 `validate → index → check` 연쇄 재파싱은 별도
  프로세스 3개), 실제로 벌어지는 "단일 커맨드 내 동일 파일 중복 파싱"도
  없음을 확인함(search/index/validate/check 전부 파일당 1회 읽기).
  진짜 도움이 되려면 mtime 키 영속 캐시가 필요한데, 이는 staleness 리스크
  대비 ADR 실사용 규모(수백 개 미만, 감사 보고서 자체 진단)에 비해
  과한 투자. (감사 보고서 §2.3 3.2)

### Low

두 개의 서로 다른 출처가 섞여 있어 각 항목에 출처를 명시했다.

**출처: `docs/adr-toolkit-audit-report.md`의 🟢 Low 리스크 항목** — 남은
건 1건뿐:

- [ ] *(전제조건: Antigravity CLI가 공개 패키지 레지스트리 지원)*
  **harness-parity CI에 Antigravity 편입** — `adapters/antigravity/README.md`
  기준 여전히 "Manually verified"뿐, agy 자체가 아직 공개 패키지 레지스트리를
  지원하지 않음 — 전제조건 미충족. (감사 보고서 §2.1 1.2)

**출처: `docs/enterprise-adoption.md` §4/§6-9** — 코드/아키텍처 감사와는
별개의, 조직 도입·거버넌스 성숙도를 다루는 문서. 아래 항목 대부분은
코드로 "구현"할 수 있는 게 아니라 실제 세계의 전제조건(저장소 public
전환, 유지관리자 인원, 저장소 개수)에 막혀 있으니, 시작 전에
전제조건부터 확인할 것.

- [ ] *(전제조건: 저장소 public 전환)* **Public 전환 게이트 실제 적용** — PR template/`CONTRIBUTING.md`/`SECURITY.md`는 이미 존재함. 남은 건 `master`/`develop`/`v*` 태그에 대한 실제 GitHub ruleset(PR 필수, required CI, conversation resolution, force-push/삭제 차단) 적용과 API로 실제 상태 재조회뿐 — 코드 작업이 아니라 저장소를 public 전환한 뒤 GitHub 설정/API에서 해야 하는 작업. `project_v1_public_release_plan` 메모리 참고(1.0.0 시점 public 전환 계획). (enterprise-adoption.md §4, §9)
- [ ] *(전제조건: qualified maintainer 2명 이상)* **CODEOWNERS 독립 승인 활성화** — 현재 1인 운영 상태에서 필수 code-owner review를 켜면 운영을 막거나 형식적 self-review만 만든다고 보고서 자체가 명시적으로 경고함. 인원 조건 충족 전엔 시작하지 않음. (enterprise-adoption.md §4, §9 "지금 구현하지 않을 것")
- [ ] *(전제조건: 저장소 2개 이상)* **조직 단위 ruleset/reusable workflow/audit export/taxonomy** — 여러 저장소가 같은 운영 문제를 반복할 때 설계 시작. 지금은 저장소가 1개뿐이라 시작 조건 미충족. (enterprise-adoption.md §6, §8 항목 5)

## Done

Normally this section stays empty between sessions (resolved items live in
`changelog.md` + git history instead, and this session's own architectural
decisions in `docs/decisions/ADR-0012..0016`).
