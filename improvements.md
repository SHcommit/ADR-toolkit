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

### Low

두 개의 서로 다른 출처가 섞여 있어 각 항목에 출처를 명시했다.

**출처: `docs/adr-toolkit-audit-report.md`의 🟢 Low 리스크 항목 8개 중,
"추가 조치 불요"이거나 이번 세션/`origin/develop` 병합으로 이미 해소된
것(1.3 관련 없음, 6.1, 8.3, 8.4 PR 제목 체크는 `pr-title-check` job으로
이미 존재, 5.3의 README 이스케이프 비일관성은 이번 세션 `safe_md_link_text`
작업으로 이미 해소)을 제외하고, 실제로 아직 안 한 것만 남긴 4건:**

- [ ] *(전제조건: Antigravity CLI가 공개 패키지 레지스트리 지원)*
  **harness-parity CI에 Antigravity 편입** — 현재 Codex/Gemini만 CI에서
  실제 설치까지 검증하고 Antigravity(`agy`)는 README에 "수동 검증"으로
  명시됨. `agy` 작업 자체는 다른 브랜치 소관이라 이 항목도 그쪽과 함께
  검토. (감사 보고서 §2.1 1.2)
- [ ] **CODEOWNERS로 `constraints:` 블록 보호 문서화** — 격리 계층 대신
  프로세스 통제로: ADR 디렉터리의 `constraints:` 블록을 승인 권한자만
  병합하도록 `CONTRIBUTING.md`에 명문화. 코드 변경 없이 문서 한 줄이면
  됨 — 지금 바로 가능. (감사 보고서 §2.2 2.1)
- [ ] **`proposed → deprecated` 전이 추가** — `core/lifecycle.py`의
  `ALLOWED_TRANSITIONS["proposed"]`에 `"deprecated"` 한 줄 추가 +
  `test_lifecycle.py`에 파라미터 1건 추가. 합의 없이 제안을 철회하는
  실무 케이스 지원. 아키텍처 변경 불요, 지금 바로 가능. (감사 보고서
  §2.5 5.1)
- [ ] **CHECK 사전 린트를 CREATE/STATUS 시점으로 앞당기기** — 현재는
  `constraints:` 블록 오탈자(ReDoS 포함)가 CHECK 실행 시점에야 발견됨.
  `validate.py`에 이미 있는 파싱 흐름을 `create.py`/`status.py` 종료
  직전에도 실행해 ADR 작성 시점에 조기 경고. (감사 보고서 §2.5 5.2)

**출처: `docs/enterprise-adoption.md` §4/§6-9** — 코드/아키텍처 감사와는
별개의, 조직 도입·거버넌스 성숙도를 다루는 문서. 아래 항목 대부분은
코드로 "구현"할 수 있는 게 아니라 실제 세계의 전제조건(저장소 public
전환, 유지관리자 인원, 저장소 개수)에 막혀 있으니, 시작 전에
전제조건부터 확인할 것.

- [ ] *(전제조건: 저장소 public 전환)* **Public 전환 게이트 실제 적용** — PR template/`CONTRIBUTING.md`/`SECURITY.md`는 이미 존재함(v0.2.1에 포함, `origin/develop` 병합으로 확인). 남은 건 `master`/`develop`/`v*` 태그에 대한 실제 GitHub ruleset(PR 필수, required CI, conversation resolution, force-push/삭제 차단) 적용과 API로 실제 상태 재조회뿐 — 코드 작업이 아니라 저장소를 public 전환한 뒤 GitHub 설정/API에서 해야 하는 작업. `project_v1_public_release_plan` 메모리 참고(1.0.0 시점 public 전환 계획). (enterprise-adoption.md §4, §9)
- [ ] *(전제조건: qualified maintainer 2명 이상)* **CODEOWNERS 독립 승인 활성화** — 현재 1인 운영 상태에서 필수 code-owner review를 켜면 운영을 막거나 형식적 self-review만 만든다고 보고서 자체가 명시적으로 경고함. 인원 조건 충족 전엔 시작하지 않음. (enterprise-adoption.md §4, §9 "지금 구현하지 않을 것")
- [ ] *(전제조건: 저장소 2개 이상)* **조직 단위 ruleset/reusable workflow/audit export/taxonomy** — 여러 저장소가 같은 운영 문제를 반복할 때 설계 시작. 지금은 저장소가 1개뿐이라 시작 조건 미충족. (enterprise-adoption.md §6, §8 항목 5)
- [ ] **도입 지표(adoption metrics) 수집 스크립트** — decision lead time, exception age, unresolved violations 같은 지표는 이미 존재하는 ADR frontmatter(`date`, `status`)와 exception JSON(`created`, `expiry`)만으로 계산 가능해 public 전환이나 멀티레포 없이도 지금 시작할 수 있음. 다만 "이 지표를 수집한다는 사실만으로 성숙도가 올라가지 않는다"는 보고서 자체의 경고를 유념 — 지표 정의 버전 관리, 실제 운영 개선 연결까지 되어야 의미가 있음. (enterprise-adoption.md §7)

## Done

Normally this section stays empty between sessions (resolved items live in
`changelog.md` + git history instead). Populated once here as a
cross-session handoff summary at the owner's explicit request — clear this
back out next time a session does routine cleanup, per the usual rule.

All of it is on branch `feature/analyzing-adr-toolkit`, not merged/PR'd
into `develop` yet (owner's explicit choice: keep as-is). `origin/develop`
was merged **into** this branch (not the other way around) to pick up its
`v0.2.1` release, Antigravity plugin work, and CI additions — see
`handoff.md` for the 3-file conflict resolution. Full detail, code, and
rationale for every hardening item lives in
`docs/adr-toolkit-audit-report.md` and the 3 (gitignored) plan files under
`docs/superpowers/plans/2026-09-01-*`.

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

Test suite: 395 → 465 passing (this branch's own work), zero regressions;
469 passing after merging `origin/develop`'s own new tests in. CI gained
a `type-check` job and an 85% coverage gate (this branch), plus
`examples-drift` and `pr-title-check` jobs (from `origin/develop`).
