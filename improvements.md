# improvements.md

Concrete implementation backlog. Unscheduled product bets belong in
`project-roadmap.md`; current-session state belongs in `handoff.md`.

## Open

Backlog derived from `docs/adr-toolkit-audit-report.md`. Scope for this
worktree excludes domains 1 (core/plugin architecture) and 5 (governance/
FSM) — already scored 72/80 and mostly "no action needed" in the audit —
plus anything Antigravity-adapter-related, automatic version sync, and
README prose, which are being handled in other worktrees/branches. The two
items below flagged "(다른 워크트리 확인)" touch files those efforts may
also touch.

### Critical

**구현 계획**: `docs/superpowers/plans/2026-09-01-critical-hardening.md`
(Task 1-8, TDD 단계별). 세션이 끊겨도 이 계획 파일의 체크박스 +
`git log --oneline`에 남는 태스크별 커밋 메시지로 어디까지 됐는지 바로
알 수 있다 — 상세 재개 절차는 `handoff.md` 참고.

- [ ] **원자적 파일 쓰기 + ID 채번 락** — `identifiers.py`, `create.py`,
  `exception.py`, `supersede.py`; 신규 `core/atomic_io.py`. 락 없는
  glob→max+1 채번과 비원자적 `write_text`를 `adr_directory_lock` +
  `atomic_write_text`로 교체. (감사 보고서 §1 Top-3 #1, §2.3 3.3)
- [ ] **ADR 정규식 ReDoS 가드** — `rules/conflict.py`. `constraints:`의
  `pattern` 필드 실행에 하드 타임아웃(POSIX: SIGALRM, Windows: 정적
  중첩 정량자 린트). (감사 보고서 §1 Top-3 #2, §2.2 2.3)
- [ ] **생성된 README 링크 이스케이프** — `core/rendering.py`,
  `commands/index.py`. `render_mermaid`의 `_mermaid_label`처럼 title을
  이스케이프해 `docs/decisions/README.md` 생성 시 링크 하이재킹 방지.
  자동 생성 코드 수정이며 사람이 쓰는 README 문서 작업과는 무관.
  (감사 보고서 §1 Top-3 #2, §2.2 2.3)
- [ ] **구조화 로깅** — 신규 `core/telemetry.py`, `adr.py`. stderr에
  JSON 로그(operation, correlation_id, exception type) 추가, stdout의
  순수 JSON 결과 계약은 불변 유지. (감사 보고서 §1 Top-3 #3, §2.7 7.1)

### High

- [ ] **저장소 경로 탈출 방지** — `core/repository_paths.py`.
  `--dir`/`--root`가 저장소 루트 밖을 가리키지 못하도록 경계 검사.
  (감사 보고서 §2.2 2.3)
- [ ] **테스트 커버리지 측정 도입** — `.github/workflows/test.yml`에
  `pytest-cov --cov-branch --cov-fail-under=85` 추가. `release.yml`은
  건드리지 않음. (감사 보고서 §2.8 8.1)
- [ ] **mypy + TypedDict 계약 타이핑** — 신규 `core/contracts.py`, CI에
  `mypy --strict` 게이트. (감사 보고서 §2.4 4.1)
- [ ] **진단/타이밍 모드** — `adr.py`에 `--diagnostic` 플래그로 실행
  시간 계측 노출. (감사 보고서 §2.7 7.2)
- [ ] **카오스(SIGKILL) 복원력 테스트** — 원자적 쓰기 완료 후, 쓰기
  도중 강제 종료 시 ADR 파일이 항상 유효 상태인지 검증하는 테스트 추가.
  (감사 보고서 §2.8 8.2)
- [ ] **어댑터 매니페스트 검증기 추출 (코드만)** — 신규
  `scripts/adapter_sdk.py`의 `validate_adapter_manifest`. 튜토리얼
  문서화는 README 작업 쪽에서 처리. (감사 보고서 §2.6 6.3)
- [ ] *(다른 워크트리 확인)* **공급망 보안(체크섬/서명)** —
  `.github/workflows/release.yml`에 SHA-256/Sigstore 서명 단계. 자동
  버전 동기화 작업이 같은 파일을 건드릴 수 있어 그쪽에 붙이는 것을 권장.
  (감사 보고서 §2.2 2.2)
- [ ] *(다른 워크트리 확인)* **8.4 자동 버전 산정 방향 재검토** — 감사
  보고서 원 권고는 "semantic-release류 자동 버전 산정 강제 도입
  비권장"이었음. 진행 중인 자동 버전 동기화 작업 방향과 배치되지 않는지
  확인. (감사 보고서 §2.8 8.4)

### Medium

- [ ] **런타임 스키마 단일 진실 소스화** — `core/schema.py`를
  `schemas/adr.schema.json`/`exception.schema.json` 기반 `jsonschema`
  검증으로 재작성해 스키마 드리프트 제거. (감사 보고서 §2.4 4.2)
- [ ] **공통 에러 베이스 클래스** — `AdrToolkitError`로 기존 5개 예외
  클래스 통합, `error_code`를 클래스 속성화. 구조화 로깅 작업과 함께
  진행하면 자연스러움. (감사 보고서 §2.4 4.3)
- [ ] **출력 계약 스키마 고정(골든 파일)** — 16개 커맨드 출력에 대한
  JSON Schema 스냅샷 테스트, 4.2 작업과 파일 공유 가능. (감사 보고서
  §2.1 1.3 — 도메인 1 제외 대상이지만 4.2와 묶어 진행 시 예외적으로 포함)
- [ ] **파싱 결과 캐시** — `functools.lru_cache` 기반 프로세스 내
  재파싱 제거. (감사 보고서 §2.3 3.2)
- [ ] **대량 ADR 벤치마크** — 2,000개 픽스처로 `search`/`index` 실행
  시간 측정, CI 회귀 임계값 설정. (감사 보고서 §2.3 3.1)
- [ ] **CLI TTY 인지 출력** — stderr에 사람이 읽을 요약 라인(비-TTY
  시 무출력). (감사 보고서 §2.6 6.2)

## Done

Resolved items are recorded in `changelog.md` (what shipped) and git history
(exactly how) rather than kept here — this section stays empty between
sessions.
