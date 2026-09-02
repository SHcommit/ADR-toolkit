# improvements.md

Concrete implementation backlog. Unscheduled product bets belong in
`project-roadmap.md`; current-session state belongs in `handoff.md`.

## Open

Backlog derived from `docs/adr-toolkit-audit-report.md`. Scope excludes
domains 1 (core/plugin architecture) and 5 (governance/FSM) — already
scored 72/80 and mostly "no action needed" in the audit. README prose is
another worktree's.

### High

None open.

### Medium

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
