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

## Done

Normally this section stays empty between sessions (resolved items live in
`changelog.md` + git history instead). Populated once here as a
cross-session handoff summary at the owner's explicit request — clear this
back out next time a session does routine cleanup, per the usual rule.

All of it is on branch `feature/analyzing-adr-toolkit`, not merged/PR'd
yet (owner's explicit choice: keep as-is). Full detail, code, and
rationale for every item lives in `docs/adr-toolkit-audit-report.md` and
the 3 (gitignored) plan files under `docs/superpowers/plans/2026-09-01-*`.

**Critical** — atomic writes + directory locking (`core/atomic_io.py`,
wired into create/exception/supersede so concurrent invocations can't
duplicate ADR/exception IDs or corrupt files); ReDoS timeout guard on
CHECK's author-supplied regex patterns; Markdown link-injection escape in
the generated `docs/decisions/README.md`; structured stderr logging with
correlation IDs (`core/telemetry.py`).

**High** — `--dir`/`--root` path-escape guard (`PathEscapesRootError`);
CI branch-coverage gate at 85% (measured baseline: 93.32%); `mypy --strict`
CI gate + `core/contracts.py` (typed result shapes); `adr.py --diagnostic`
timing flag; OS-level (fork+SIGKILL) proof that a mid-write crash never
tears an ADR file; shared adapter-manifest validator
(`scripts/adapter_sdk.py`) used by all 4 manifest-based harness adapters.

**Medium** — common `AdrToolkitError` base class for all 6 domain
exceptions (also closed a gap: `PathEscapesRootError` was raised but never
actually caught at any of its 7 call sites until this pass); schema-drift
regression test between `schemas/*.json` and the runtime validators (no
`jsonschema` dependency added, by design); bulk-ADR (200 fixtures)
performance sanity check; TTY-only human summary line on stderr
(`ADR_TOOLKIT_NO_COLOR` to suppress); `core/contracts.py` extended from
2/16 to 16/16 commands.

**Declined, not done** — parsing-result caching (`functools.lru_cache`):
this CLI is a fresh process per invocation, so an in-process cache can't
reduce the actual cross-invocation re-parsing the audit worried about, and
no single command re-parses a file more than once internally either. Left
as a Critical-domain note in `docs/adr-toolkit-audit-report.md`, not
reopened without a real usage signal that changes this analysis.

Test suite: 395 → 465 passing, zero regressions. CI gained a `type-check`
job and an 85% coverage gate.
