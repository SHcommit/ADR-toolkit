# improvements.md

Concrete implementation backlog. Unscheduled product bets belong in
`project-roadmap.md`; current-session state belongs in `handoff.md`.

## Open

Backlog derived from `docs/adr-toolkit-audit-report.md`, operational experiences, and developer friction analysis.

### High

- [ ] **ReDoS 크로스 플랫폼 Guard (Windows 비-POSIX 타임아웃)** — `rules/conflict.py`의 정규식 ReDoS 타임아웃 구동 방식이 `signal.SIGALRM` 기반이라 POSIX 전용 환경으로 제한됨. Static constraint checker (`core/constraints.py`) 외 교차 정규식 타임아웃을 Windows에서도 안전하게 처리할 수 있도록 스레드/프로세스 타임아웃 워커 도입. (`handoff.md` Open Risk 대응)
- [ ] **ADR `supersede` 2단계 원자적 트랜잭션 롤백 보장** — `supersede` 커맨드가 기존 ADR 상태 변경(Superseded)과 신규 ADR 생성/수정(Superseding)을 연쇄 실행할 때, 프로세스 중간 강제 종료 시 발생할 수 있는 '반쪽짜리 업데이트' 방지를 위한 트랜잭션 백업/롤백 안전장치 구축.

### Medium

- [ ] **ADR 중첩/유사도 감지 및 파편화 방지 Eval 시스템** — 작성하려 하거나 기존에 존재하는 ADR 간 내용/주제/영향 범위의 중첩(overlap) 및 파편화를 사전 감지하는 로직과, ADR 집합의 중복·충돌·일관성을 지속해서 평가/검증하는 Evaluation 프레임워크 구축. (유사도 기반 `supersede` 권장, 중복 작성 방지)
- [ ] **개발용 플러그인 메인 저장소 Symlink 자동화 스크립트** — local development 시 `~/.gemini/config/plugins/adr-toolkit`이 임시 워크트리가 아닌 메인 저장소를 항상 바라보도록 하고, 버전 갱신 시 symlink 유효성을 체크하는 도구/가이드 정립.
- [ ] **주간 자동 ADR 헬스체크 및 무효화/깨진 링크 점검 오토메이션** — 주 1회(GitHub Actions Scheduled Workflow 등) 실행되어 오래 방치된 `PROPOSED` ADR, 리팩터링으로 깨진 `affected_paths` 경로, 버전 드리프트를 자동 점검하고 이슈/알림을 생성하는 주간 유지보수 시스템.
- [ ] **PR 시 아키텍처 영향도 자동 판별 및 ADR 작성 유도 (Significance Bot)** — 중요 경계 코드 수정 시 ADR 누락을 PR 체크 단계에서 감지하고 관련 ADR 템플릿과 초안 생성을 자동 가이드하는 CI 봇 연동.
- [ ] **Frontmatter 자동 교정 및 린터 (`adr lint --fix`)** — 사용자가 손으로 수정하며 발생하는 프론트매터 오탈자, 필수 태그/날짜 누락, 들여쓰기 오류 등을 안전하게 자동 보정하는 UX 개선 기능.
- [ ] **대화형 의존성 시각화 뷰어 (`adr graph --format=html`)** — 현 mermaid/json 출력 외에도 단일 HTML/SVG 파일로 ADR 간의 이행/대체/참조 그래프를 브라우저에서 인터랙티브하게 탐색할 수 있는 뷰어 기능.
- [ ] **코드 드리프트 자동 탐지 (`adr drift`)** — ADR 작성 날짜 및 `affected_paths`의 실제 `git log` 변경 이력을 교차 분석하여, ADR 합의 시점 이후 지침과 다르게 변경된 코드 영역을 추적·리포팅하는 서브커맨드.

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
