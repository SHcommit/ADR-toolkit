# improvements.md

Concrete implementation backlog. Unscheduled product bets belong in
`project-roadmap.md`; current-session state belongs in `handoff.md`.

## Open

Backlog derived from `docs/adr-toolkit-audit-report.md`. Scope for this
worktree excludes domains 1 (core/plugin architecture) and 5 (governance/
FSM) — already scored 72/80 and mostly "no action needed" in the audit.
The Antigravity-adapter and automatic-version-sync work that used to be
a separate worktree has since been merged via GitHub PR #6/#7 into
`origin/develop`, which this branch pulled in (`0a0db8a`) — "다른
워크트리 확인" items were re-checked against that merged code and either
closed out or reworded below. README prose is still another worktree's.

### High

- [ ] **공급망 보안(체크섬/서명)** — `.github/workflows/release.yml`
  확인 결과 여전히 테스트/버전 체크/릴리스 생성만 있고 SHA-256/Sigstore
  서명 단계는 없음. 더 이상 다른 워크트리가 이 파일을 동시에 만지고
  있지 않으므로(그 작업은 이미 병합됨) 이제 이 워크트리에서 진행 가능 —
  다만 릴리스 파이프라인(운영 인프라)을 건드리는 작업이라 시작 전
  오너 확인 필요. (감사 보고서 §2.2 2.2)

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
"추가 조치 불요"이거나 이미 해소된 것을 제외하고 실제로 안 한 것 4건
중 3건 완료(`0307a1c`, `9a44342`). 남은 건 1건뿐:**

- [ ] *(전제조건: Antigravity CLI가 공개 패키지 레지스트리 지원)*
  **harness-parity CI에 Antigravity 편입** — agy 관련 작업(PR #6)은
  이미 병합됐지만 `adapters/antigravity/README.md`를 재확인한 결과 여전히
  "Manually verified"뿐, agy 자체가 아직 공개 패키지 레지스트리를
  지원하지 않음 — 전제조건 그대로 미충족. (감사 보고서 §2.1 1.2)

**출처: `docs/enterprise-adoption.md` §4/§6-9** — 코드/아키텍처 감사와는
별개의, 조직 도입·거버넌스 성숙도를 다루는 문서. 아래 항목 대부분은
코드로 "구현"할 수 있는 게 아니라 실제 세계의 전제조건(저장소 public
전환, 유지관리자 인원, 저장소 개수)에 막혀 있으니, 시작 전에
전제조건부터 확인할 것.

- [ ] *(전제조건: 저장소 public 전환)* **Public 전환 게이트 실제 적용** — PR template/`CONTRIBUTING.md`/`SECURITY.md`는 이미 존재함(v0.2.1에 포함, `origin/develop` 병합으로 확인). 남은 건 `master`/`develop`/`v*` 태그에 대한 실제 GitHub ruleset(PR 필수, required CI, conversation resolution, force-push/삭제 차단) 적용과 API로 실제 상태 재조회뿐 — 코드 작업이 아니라 저장소를 public 전환한 뒤 GitHub 설정/API에서 해야 하는 작업. `project_v1_public_release_plan` 메모리 참고(1.0.0 시점 public 전환 계획). (enterprise-adoption.md §4, §9)
- [ ] *(전제조건: qualified maintainer 2명 이상)* **CODEOWNERS 독립 승인 활성화** — 현재 1인 운영 상태에서 필수 code-owner review를 켜면 운영을 막거나 형식적 self-review만 만든다고 보고서 자체가 명시적으로 경고함. 인원 조건 충족 전엔 시작하지 않음. (enterprise-adoption.md §4, §9 "지금 구현하지 않을 것")
- [ ] *(전제조건: 저장소 2개 이상)* **조직 단위 ruleset/reusable workflow/audit export/taxonomy** — 여러 저장소가 같은 운영 문제를 반복할 때 설계 시작. 지금은 저장소가 1개뿐이라 시작 조건 미충족. (enterprise-adoption.md §6, §8 항목 5)

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

**Low (audit-report-sourced, 3 of 4)** — `constraints:` block review
documented in `CONTRIBUTING.md`; `proposed → deprecated` lifecycle
transition added; CHECK's constraints-block lint moved earlier to
CREATE/STATUS time (`core/constraints.lint()`, new `warnings` field on
`CreateResult`/`StatusResult`) so a typo surfaces at authoring time
instead of only when CHECK later runs against it. The 4th item
(Antigravity in harness-parity CI) stays open, blocked on `agy` getting a
public package registry.

- [x] **도입 지표(adoption metrics) 수집 스크립트** —
  `scripts/adoption_metrics.py`가 `docs/enterprise-adoption.md` §7의 다섯
  지표를 JSON으로 계산한다. ADR/exception 스냅샷, 로컬 Git, 명시적 JSONL,
  CHECK 스냅샷, 선택적 GitHub 리뷰 근거를 지원하며 불완전한 근거는
  coverage/availability/warning으로 노출한다. (`9a0de45`..`f814d64`)

**Windows ReDoS static complexity linter** (promoted from `handoff.md`'s
Open Risks, not originally a numbered backlog item) — `core/constraints.py`
now statically rejects a nested-quantifier `pattern` value (e.g. `(a+)+`)
at parse time for `forbidden_import`/`dependency_forbidden` rules, closing
the gap where `rules/conflict.py`'s runtime SIGALRM timeout guard is
POSIX-only and Windows had zero ReDoS protection. Heuristic, not a full
detector -- alternation-based ReDoS shapes remain uncaught.

**8.4 자동 버전 산정 방향 재검토 — reviewed, closed, no code change.**
The Antigravity/version-sync worktree's work merged in via PR #6/#7
(`origin/develop`, pulled into this branch at `0a0db8a`). Re-checked
`scripts/sync_version.py` and `.github/workflows/release.yml` against the
audit's original recommendation ("manual version bump, don't force
semantic-release-style automation") -- confirmed no conflict: versioning
is still manual (`VERSION` file + `sync_version.py --check`), no
auto-bump tooling was introduced. Removed from Open; the supply-chain
signing item stays open (verified not implemented) but no longer flagged
"다른 워크트리 확인" since that worktree's work is already merged.

Test suite: 395 → 465 passing (this branch's own work), zero regressions;
469 after merging `origin/develop`; 479 after the Low-priority follow-up
work; 518 as of this note (includes a parallel Codex session's own
adoption-metrics commits landing in this same branch -- see `handoff.md`,
not itemized here since that work isn't this session's to describe). CI
gained a `type-check` job and an 85% coverage gate (this branch), plus
`examples-drift` and `pr-title-check` jobs (from `origin/develop`).
