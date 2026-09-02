# improvements.md

Concrete implementation backlog. Unscheduled product bets belong in
`project-roadmap.md`; current-session state belongs in `handoff.md`.

## Open

Backlog derived from `docs/adr-toolkit-audit-report.md`. Scope excludes
domains 1 (core/plugin architecture) and 5 (governance/FSM) — already
scored 72/80 and mostly "no action needed" in the audit. README prose is
another worktree's.

### Low

두 개의 서로 다른 출처가 섞여 있어 각 항목에 출처를 명시했다.

**출처: `docs/enterprise-adoption.md` §4/§6-9** — 코드/아키텍처 감사와는
별개의, 조직 도입·거버넌스 성숙도를 다루는 문서. 아래 항목 대부분은
코드로 "구현"할 수 있는 게 아니라 실제 세계의 전제조건(저장소 public
유지관리자 인원, 저장소 개수)에 막혀 있으니, 시작 전에 전제조건부터
확인할 것.

- [ ] *(전제조건: qualified maintainer 2명 이상)* **CODEOWNERS 독립 승인 활성화** — 현재 1인 운영 상태에서 필수 code-owner review를 켜면 운영을 막거나 형식적 self-review만 만든다고 보고서 자체가 명시적으로 경고함. 인원 조건 충족 전엔 시작하지 않음. (enterprise-adoption.md §4, §9 "지금 구현하지 않을 것")
- [ ] *(전제조건: 저장소 2개 이상)* **조직 단위 ruleset/reusable workflow/audit export/taxonomy** — 여러 저장소가 같은 운영 문제를 반복할 때 설계 시작. 지금은 저장소가 1개뿐이라 시작 조건 미충족. (enterprise-adoption.md §6, §8 항목 5)

## Done

Normally this section stays empty between sessions (resolved items live in
`changelog.md` + git history instead, and this session's own architectural
decisions in `docs/decisions/ADR-0012..0016`).
