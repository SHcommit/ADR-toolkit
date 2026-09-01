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

### High

- [ ] *(다른 워크트리 확인)* **공급망 보안(체크섬/서명)** —
  `.github/workflows/release.yml`에 SHA-256/Sigstore 서명 단계. 자동
  버전 동기화 작업이 같은 파일을 건드릴 수 있어 그쪽에 붙이는 것을 권장.
  (감사 보고서 §2.2 2.2)
- [ ] *(다른 워크트리 확인)* **8.4 자동 버전 산정 방향 재검토** — 감사
  보고서 원 권고는 "semantic-release류 자동 버전 산정 강제 도입
  비권장"이었음. 진행 중인 자동 버전 동기화 작업 방향과 배치되지 않는지
  확인. (감사 보고서 §2.8 8.4)

### Medium

- [ ] ~~**파싱 결과 캐시**~~ — **결정: 하지 않음.** 이 CLI는 호출마다
  새 프로세스라 `functools.lru_cache`는 프로세스 간 재파싱을 전혀 줄이지
  못하고(원 문제였던 `validate → index → check` 연쇄 재파싱은 별도
  프로세스 3개), 실제로 벌어지는 "단일 커맨드 내 동일 파일 중복 파싱"도
  없음을 확인함(search/index/validate/check 전부 파일당 1회 읽기).
  진짜 도움이 되려면 mtime 키 영속 캐시가 필요한데, 이는 staleness 리스크
  대비 ADR 실사용 규모(수백 개 미만, 감사 보고서 자체 진단)에 비해
  과한 투자. (감사 보고서 §2.3 3.2)
- [ ] **출력 계약 스키마 고정(골든 파일)** — `CreateResult`, `CheckResult`
  두 개만 커버됨. 나머지 14개 커맨드는 여전히 미착수. (감사 보고서 §2.1
  1.3)

## Done

Resolved items are recorded in `changelog.md` (what shipped) and git history
(exactly how) rather than kept here — this section stays empty between
sessions.
