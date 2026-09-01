# ADR Toolkit 전수 감사 보고서

**대상**: ADR Toolkit v0.2.0 (`skills/adr-toolkit`)
**브랜치**: `feature/analyzing-adr-toolkit`
**감사 방식**: 정적 코드 감사 + 테스트/CI 구성 검증 (실제 소스코드 대조 검증)
**일자**: 2026-08-31

---

## ⚠ 전제 정정 — 감사 착수 전 필수 확인 사항

본 감사 요청서는 **Node.js/TypeScript 기반의 런타임 플러그인 로딩 시스템**(npm 패키지, VM/WASM 샌드박스, 서드파티 코드 실행)을 전제로 설계되었다. 그러나 실제 대상 시스템은 **Python 3.9+ 단일 프로세스 CLI**(약 3,000 LOC, `skills/adr-toolkit/scripts/`)이며, "플러그인"에 해당하는 것은 Claude Code / Codex / Gemini CLI / Antigravity용 **정적 매니페스트(adapter)** 4종뿐이다 — 이들은 동일한 Python 스크립트를 가리키는 설치 경로 지정자일 뿐, 런타임에 로드되는 제3자 실행 코드가 아니다.

따라서 VM 격리·WASM 샌드박스·플러그인 서명 검증 같은 항목은 **"해당 없음(N/A)"**이 아니라 **"현재 위협 모델에서 불필요하지만, 실제 위협 표면(신뢰되지 않는 저장소 콘텐츠·ADR 파일·정규식)에 대한 방어는 별도로 존재해야 한다"**는 관점으로 재해석해 평가했다. 요청서의 TypeScript 인터페이스/팩토리 패턴 예시 역시 실제 언어인 **Python**으로 대체했다 — 이는 지시 불이행이 아니라, "객관적으로 분석하라"는 본 요청의 핵심 원칙을 따른 결과다. 이 재해석 기준은 아래 각 항목에 그대로 반영된다.

---

## 0. 종합 스코어

100점 만점. "엔터프라이즈 하드닝 완성도" 기준이며, 도구의 실제 목적(단일 저장소용 결정론적 문서화 CLI)에 대한 적합성과는 별개 축이다 — 이 도구는 **제품으로서는 이미 잘 작동**하지만, 아래 점수는 "수백 개 팀이 공유 서비스로 쓸 때도 무너지지 않는가"를 기준으로 냉정하게 매겼다.

| 영역 | 점수 | 한줄 평가 |
|---|---:|---|
| **종합 (가중평균)** | **64 / 100** | C+ · Solid Core, Hardened Edges Missing |
| 1. 코어 분리 & IoC | 72 | 내부 경계는 우수, "플러그인" 계약은 미성숙 |
| 2. 보안 & 제로트러스트 | 48 | 최저 방어선 미비 — 2번째로 취약 |
| 3. 확장성 & 성능 | 55 | 현재 규모엔 무해, 성장 시 재작성 필요 |
| 4. 타입 & 런타임 무결성 | 65 | 런타임 검증은 실재, 정적 타입 게이트는 부재 |
| 5. 거버넌스 & 컴플라이언스 | 80 | 최고 점수 — 정책-as-코드 설계가 진짜로 정교함 |
| 6. DX & 툴링 | 78 | 에이전트 우선 설계가 실제로 잘 작동함 |
| 7. 관측가능성 | 25 | 최저 점수 — 사실상 미착수 |
| 8. 테스트 & 릴리스 | 82 | 규모 대비 최고 수준의 릴리스 규율 |

---

## 1. 즉시 착수 Top 3 Critical 태스크

전체 24개 항목 중 방치 시 **데이터 무결성 손실** 또는 **보안 사고**로 직결되는 3건. 모두 실제 소스에서 재현 가능한 결함이며, 아래 순서로 착수를 권고한다.

### #1 — ADR 파일 쓰기 경로 전체가 원자적(atomic)이지 않다

**근거**: `create.py:136-174`, `identifiers.py:17-23`, `supersede.py:114-126`
**리스크**: 🔴 Critical

`identifiers.next_id()`는 디렉터리를 glob하여 최댓값+1을 계산하고, 이후 `create.py`는 `target.exists()`를 확인한 뒤 `write_text()`로 직접 쓴다. 이 세 단계 사이에 잠금(lock)이 전혀 없어 두 프로세스가 동시에 실행되면 **같은 ADR 번호가 중복 채번**되거나 한쪽 쓰기가 유실된다. 더 심각한 건 `write_text` 자체가 "임시파일 작성 후 rename" 패턴이 아니라 직접 덮어쓰기라서, 프로세스가 쓰는 도중 강제 종료(OOM kill, CI 타임아웃)되면 **ADR 파일이 반쪽만 쓰인 채 손상**된다. `supersede.py`의 2-파일 갱신은 두 번째 쓰기 실패 시 첫 번째를 되돌리려 시도하지만, 프로세스가 그 사이에 죽으면 롤백 코드 자체가 실행되지 않아 두 ADR이 서로 어긋난 상태로 영구 고정된다.

**솔루션**:

```python
# scripts/core/atomic_io.py — 신규 모듈
import os, sys, tempfile
from pathlib import Path
from contextlib import contextmanager

if sys.platform == "win32":
    import msvcrt
    def _lock(fd): msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
    def _unlock(fd):
        try: msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError: pass
else:
    import fcntl
    def _lock(fd): fcntl.flock(fd, fcntl.LOCK_EX)
    def _unlock(fd): fcntl.flock(fd, fcntl.LOCK_UN)

def atomic_write_text(path: Path, content: str, *, encoding="utf-8") -> None:
    """임시 파일에 쓰고 fsync 후 os.replace — 크래시 시 원본 파일은
    항상 이전 버전이거나 새 버전, 절대 반쪽이 아니다."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)  # POSIX/Windows 모두 원자적
    except BaseException:
        Path(tmp).unlink(missing_ok=True); raise

@contextmanager
def adr_directory_lock(adr_dir: Path):
    """ID 채번 + 파일 생성을 하나의 임계구역으로 묶는다 (TOCTOU 창 제거)."""
    adr_dir.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(adr_dir / ".adr-toolkit.lock", os.O_CREAT | os.O_RDWR)
    try:
        _lock(lock_fd)
        yield
    finally:
        _unlock(lock_fd); os.close(lock_fd)
```

`create.py`는 `next_id()` 계산부터 `write_text`까지를 `with adr_directory_lock(adr_dir):` 블록 안에 넣고, 모든 쓰기 지점을 `atomic_write_text`로 교체한다. `supersede.py`의 2-파일 갱신도 같은 락 안에서 두 `atomic_write_text` 호출로 바뀌면, 프로세스가 어느 지점에서 죽어도 파일 시스템은 항상 "갱신 전" 또는 "갱신 후" 둘 중 하나의 유효한 상태에 머문다(롤백 코드 자체가 불필요해진다).

**IMPACT**: 병렬 CI/에이전트 실행 시 ADR 번호 충돌, 크래시 시 저장소의 단일 진실 소스(decision log) 영구 손상

---

### #2 — ADR 본문이 두 개의 서로 다른 신뢰 경계를 뚫고 실행 가능 콘텐츠가 된다

**근거**: `index.py:97,109,121,127`, `rules/conflict.py:59-66`
**리스크**: 🔴 Critical

(a) **Markdown 인젝션**: `index.py`의 README 생성 코드는 ADR의 `title`을 이스케이프 없이 `f"[{entry['id']} — {entry['title']}]({entry['filename']})"` 형태로 직접 삽입한다. 같은 모듈의 `render_mermaid`는 `_mermaid_label`에서 `html.escape`와 대괄호 치환을 하는데, README 인덱스 렌더러만 이 처리가 빠져 있다 — title에 `) [클릭](https://evil.example` 같은 문자열을 넣으면 인덱스의 링크 타깃을 조작할 수 있다.

(b) **ReDoS**: `conflict.py::_content_pattern`는 ADR 저자가 작성한 `constraints:` 블록의 `pattern` 필드를 그대로 `re.compile`하여 diff의 모든 추가 라인에 대해 매칭한다. 타임아웃도 복잡도 검사도 없어 `(a+)+$` 류의 패턴 하나가 CI의 CHECK 단계를 무한정 멈추게 할 수 있다.

**솔루션**:

```python
# scripts/core/rendering.py 에 추가
import re

_MD_LINK_UNSAFE = re.compile(r"[\[\]\\]")

def safe_md_link_text(text: str) -> str:
    """[] \ 를 이스케이프하고 개행을 공백으로 접어 링크 구문 탈출을 막는다."""
    return _MD_LINK_UNSAFE.sub(r"\\\g<0>", str(text)).replace("\n", " ")
```

```python
# scripts/rules/conflict.py — 패턴 실행에 하드 타임아웃
import signal, sys

class RegexTimeout(Exception): pass

def _guarded_search(regex, line, timeout_s=0.25):
    if sys.platform == "win32":
        return regex.search(line)  # SIGALRM 부재 — 대신 컴파일 시점 정적 린트로 방어
    def _raise(*_): raise RegexTimeout()
    prev = signal.signal(signal.SIGALRM, _raise)
    signal.setitimer(signal.ITIMER_REAL, timeout_s)
    try:
        return regex.search(line)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, prev)
```

`_content_pattern`에서 `regex.search(line)` 호출을 `_guarded_search(regex, line)`로 교체하고 `RegexTimeout`을 `BAD_CONSTRAINTS` 경고로 강등한다. Windows에서는 `re` 표준 라이브러리에 타임아웃 훅이 없으므로, 컴파일 시점에 중첩 정량자(`(x+)+`, `(x*)*`) 패턴을 정적으로 거부하는 린터를 constraints.py 파싱 단계에 추가해 최소 방어선을 이중화해야 한다.

**IMPACT**: README 링크 하이재킹(피싱 유도), CI에서 CHECK 무한 행(파이프라인 전체 블로킹)

---

### #3 — 실패가 "무슨 일이 있었는지" 남기지 않는다 (관측가능성 부재)

**근거**: `adr.py:186-195` (전역 예외 핸들러)
**리스크**: 🔴 Critical

`main()`은 모든 예외를 `{"code": "INTERNAL_ERROR", "detail": str(exc)}`로 뭉개 stdout JSON 한 줄로만 내보낸다. 스택 트레이스는 어디에도 기록되지 않고, 구조화 로그·상관관계 ID·타이밍 정보가 전무하다. 24개 서브커맨드 중 어느 것이 몇 ms 걸렸는지, 어떤 파일에서 파싱이 실패했는지는 재현 전까지 알 수 없다 — CI에서 한 번 실패한 `check`를 사후 디버깅할 방법이 로컬 재현뿐이다. 이는 8대 영역 중 최저 점수(25/100)의 근본 원인이다.

**솔루션**:

```python
# scripts/core/telemetry.py — 신규 모듈
import json, logging, os, sys, time, uuid

class _JsonFormatter(logging.Formatter):
    def format(self, r):
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(r.created)),
            "level": r.levelname.lower(),
            "operation": getattr(r, "operation", None),
            "correlation_id": getattr(r, "cid", None),
            "elapsed_ms": getattr(r, "elapsed_ms", None),
            "msg": r.getMessage(),
        }
        if r.exc_info:
            payload["exc_type"] = r.exc_info[0].__name__
        return json.dumps(payload, ensure_ascii=False)

def get_logger(operation: str) -> logging.LoggerAdapter:
    logger = logging.getLogger("adr_toolkit")
    if not logger.handlers:
        h = logging.StreamHandler(sys.stderr)  # stdout은 JSON 결과 계약 전용이라 절대 오염시키지 않는다
        h.setFormatter(_JsonFormatter())
        logger.addHandler(h)
        logger.setLevel(os.environ.get("ADR_TOOLKIT_LOG_LEVEL", "INFO"))
    return logging.LoggerAdapter(logger, {"operation": operation, "cid": uuid.uuid4().hex[:12]})
```

`adr.py::main`의 `except` 블록에서 이 로거로 `logger.exception(...)`을 남기고, 그 `correlation_id`를 JSON 에러 응답의 `errors[0].correlation_id`에 그대로 포함시킨다. stdout 계약(순수 JSON)은 그대로 유지되며, stderr에만 구조화 로그가 쌓이므로 기존 소비자(에이전트/CI)를 깨지 않는다.

**IMPACT**: 프로덕션 장애 시 평균 복구 시간(MTTR) 통제 불가, 근본 원인 재현 불가능한 사고 다수 발생

---

## 2. 8대 영역별 세부 진단

### 2.1 아키텍처 탄력성 & 코어 분리 — 72/100

#### 1.1 Core-Plugin 경계 & IoC — 🟡 Medium

**진단**: ✓ 강점: `core/`(도메인 규칙) · `rules/`(정책 평가) · `evidence/`(증거 수집) · `commands/`(유스케이스)의 계층 분리가 명확하고, `commands/check.py`는 `core.constraints`·`rules.conflict`를 의존성으로 주입받는 형태라 DIP를 자연스럽게 지킨다. 다만 "플러그인"은 실제로는 `adapters/*/plugin.json` 4종의 **정적 매니페스트**일 뿐, 런타임에 로드되는 확장점(hook, event bus)이 코어에 전혀 없다 — Hexagonal Architecture의 포트/어댑터라기보다는 "동일 스크립트에 대한 배포 경로 지정자"에 가깝다.

**솔루션**: 진짜 확장점이 필요해지는 시점(예: 서드파티 CHECK 규칙 kind 추가)을 대비해 `rules/conflict.py`의 `evaluate_rule`을 레지스트리 팩토리로 승격한다:

```python
_RULE_EVALUATORS: dict[str, Callable] = {}

def register_rule_kind(kind: str):
    def _wrap(fn):
        _RULE_EVALUATORS[kind] = fn
        return fn
    return _wrap

@register_rule_kind("forbidden_import")
def _content_pattern(rule, diff_files): ...

def evaluate_rule(rule, diff_files, existing_paths):
    handler = _RULE_EVALUATORS.get(rule.get("kind"))
    return handler(rule, diff_files, existing_paths) if handler else None
```

**테스트 시나리오**:
- 미등록 `kind` 등록 후 `evaluate_rule` 호출 → 정상 평가되는지 회귀 없이 확인
- 기존 6종 kind가 레지스트리 경유로도 동일 출력을 내는지 스냅샷 비교

#### 1.2 "플러그인" 라이프사이클 거버넌스 — 🟢 Low

**진단**: 런타임 로딩·해제 개념 자체가 없으므로 좀비 프로세스/메모리 누수 위험은 실질적으로 **없다** — CLI는 커맨드 1회 실행 후 즉시 종료되는 단발성 프로세스 모델이다. 다만 `harness-parity` CI 잡(codex/gemini 실제 설치)이 "설치→실행→검증"을 자동화한 것은 사실상 라이프사이클 검증의 대체재 역할을 잘 해내고 있다.

**솔루션**: 추가 조치 불요. 다만 Antigravity 어댑터만 CI에서 실제 설치가 검증되지 않는(README에 "수동 검증"으로 명시) 비대칭이 있으므로, Antigravity CLI가 공개 패키지 레지스트리를 지원하는 시점에 harness-parity 잡에 편입할 것을 백로그에 등록.

**테스트 시나리오**: (해당 없음 — 현재 아키텍처에서 라이프사이클 결함 재현 불가)

#### 1.3 API 안정성 & SemVer 계약 — 🟠 High

**진단**: `scripts/sync_version.py`가 `VERSION` 한 곳을 4개 매니페스트에 전파하고 CI의 `version-drift` 잡이 이를 검증하는 점은 훌륭하다. 그러나 이것은 "버전 문자열 동기화"이지 **API 호환성 계약**이 아니다 — JSON 출력 스키마(`{ok, operation, errors, findings...}`)가 버전 간 바뀌어도 이를 감지·경고할 장치가 없다. 예를 들어 `check`의 `findings[].confidence` 값 집합이 바뀌면 이를 파싱하는 모든 에이전트/CI 스크립트가 조용히 깨진다. Deprecation 정책 문서도 부재.

**솔루션**: 각 커맨드 출력에 대해 JSON Schema 골든 파일을 두고, PR에서 스키마 diff를 감지해 `MAJOR` 필요 여부를 자동 판정:

```python
# tests/contract/test_output_contract.py
def test_check_output_matches_frozen_schema():
    schema = json.loads(Path("tests/contract/check.schema.json").read_text())
    result = check.run(make_args(...))
    jsonschema.validate(result, schema)  # 필드 삭제/타입 변경 시 즉시 실패
```

**테스트 시나리오**:
- 16개 커맨드 각각의 출력에 대한 골든 스키마 스냅샷 테스트
- 필드 제거·타입 변경을 인위로 주입해 스키마 테스트가 실패하는지 검증(테스트의 테스트)

---

### 2.2 샌드박싱 & 제로 트러스트 보안 — 48/100

#### 2.1 악의적 코드 격리 (Sandboxing) — 🟢 Low (재정의됨)

**진단**: 실행되는 제3자 "플러그인 코드"가 존재하지 않으므로 VM/WASM 격리는 요구사항 자체가 성립하지 않는다. 실제 위협 표면은 "신뢰되지 않는 **ADR 파일 콘텐츠**"다 — `git diff` 대상 저장소, 다수 기여자가 작성하는 `constraints:` 블록이 여기 해당한다. 코드 실행 자체는 없으나(`eval`/`exec` 사용 없음 확인됨), 정규식 실행(2.3 참고)이 사실상의 "실행 가능 콘텐츠"다.

**솔루션**: 격리 계층 신설 대신, `constraints:` 블록을 승인 권한이 있는 사람만 병합할 수 있도록 CODEOWNERS로 ADR 디렉터리를 보호할 것을 `CONTRIBUTING.md`에 명문화 — 코드가 아닌 **프로세스 통제**가 여기서는 더 적절한 방어선이다.

**테스트 시나리오**: `grep -rn "eval(\|exec(\|subprocess.*shell=True" scripts/` — CI에 정적 게이트로 편입해 회귀 방지

#### 2.2 공급망 보안 — 🟠 High

**진단**: 서드파티 npm 의존성이 없어(표준 라이브러리만 사용) 전통적 의미의 "의존성 취약점"은 표면적으로 적다 — 이는 강점이다. 그러나 설치 무결성 자체가 검증되지 않는다: `.claude-plugin/marketplace.json`·Codex/Gemini 매니페스트 어디에도 체크섬/서명이 없고, GitHub Release도 `softprops/action-gh-release`가 자동 생성 노트만 첨부할 뿐 아티팩트 서명이 없다. "복사해서 어디에나 설치"(`adapters/generic`)를 공식 배포 경로로 문서화한 점은 무결성 검증을 더 어렵게 만든다.

**솔루션**: 릴리스 워크플로에 SHA-256 매니페스트 생성 및 (가능하면) Sigstore/cosign 서명 단계 추가:

```yaml
# .github/workflows/release.yml 추가 스텝
- name: Generate checksums
  run: |
    tar -czf adr-toolkit-skill.tar.gz skills/adr-toolkit
    sha256sum adr-toolkit-skill.tar.gz > SHA256SUMS
- uses: sigstore/gh-action-sigstore-python@v3
  with: { inputs: adr-toolkit-skill.tar.gz }
```

**테스트 시나리오**: 릴리스 아티팩트 다운로드 후 `sha256sum -c SHA256SUMS` 검증을 릴리스 워크플로 자체의 마지막 스텝으로 추가(자기검증)

#### 2.3 입력 검증 및 취약점 방어 — 🔴 Critical

**진단**: ✓ 강점: `diff.py:29-34`는 `--end-of-options`를 사용해 `--since` 인자가 git 옵션으로 오인되는 인젝션(예: `--output=/tmp/PWNED`)을 이미 차단하고 있다 — 이 방어는 견고하고 모범적이다. ✓ 강점: `identifiers.validate_slug`는 `[a-z0-9-]+` 화이트리스트로 경로 조작 문자를 원천 차단한다. **그러나** §1의 Top-3 #2에 서술한 Markdown 인젝션(README 링크 하이재킹)과 ReDoS(제한 없는 사용자 정의 정규식)가 이 항목의 최대 결함이다. 추가로 `--dir`/`--root` 인자는 저장소 경계 밖 경로(`../../etc`)를 그대로 받아들여, 이 CLI가 향후 다중 테넌트 SaaS(예: PR 자동 검사 봇)로 wrapping될 경우 경로 탈출로 이어질 수 있다.

**솔루션**: Top-3 #2의 코드에 더해, `repository_paths.resolve_from_root`에 경계 검사를 추가:

```python
def resolve_from_root(root, path) -> Path:
    candidate = (Path(root) / path).resolve()
    root_resolved = Path(root).resolve()
    if not candidate.is_relative_to(root_resolved):
        raise ValueError(f"{path!r} escapes repository root {root!r}")
    return candidate
```

**테스트 시나리오**:
- `--dir ../../etc/cron.d` 전달 시 `ValueError`/구조화 에러로 거부되는지
- title에 `) [phish](http://evil` 포함된 ADR로 `index` 실행 후 생성된 README에 원본 링크 구문이 깨지지 않는지
- 10자 입력으로 5초 이상 걸리는 병리적(catastrophic backtracking) 패턴을 `constraints:`에 넣고 `check`가 0.5초 내 타임아웃 경고로 종료되는지

---

### 2.3 대규모 데이터 확장성 & 성능 — 55/100

#### 3.1 대규모 모노레포 처리량 — 🟡 Medium

**진단**: `adr_directory.iter_adr_files`는 매 커맨드 호출마다 `adr_dir.glob("*.md")`로 전체 디렉터리를 나열하고, `search.py`/`index.py`/`check.py`/`validate.py`는 각 파일을 `read_text()`로 동기 전체 로드한다. 스트리밍 파서 없음, 페이지네이션 없음. ADR은 본질적으로 사람이 쓰는 문서라 "수천 개"는 비현실적 규모지만(대형 조직도 보통 수백 개 미만), `search --limit`이 필터링 **후** 자르는 방식이라 결과 상한과 무관하게 항상 O(N) 전체 스캔이 발생하는 점은 실제로 개선 여지가 있다.

**솔루션**: 즉각적인 아키텍처 재작성보다 우선순위는 낮음. N>500 도달 시를 대비해 §3.2의 캐시 계층 도입을 선행 조건으로 명시.

**테스트 시나리오**: ADR 2,000개 픽스처로 `search`/`index` 실행 시간 벤치마크, CI에 회귀 임계값(예: 3초) 설정

#### 3.2 인덱싱 & 지연 평가 — 🟡 Medium

**진단**: 캐싱 계층이 전혀 없다 — 같은 저장소에 대해 `search`를 10번 호출하면 10번 모두 전체 파일을 재파싱한다. Content-hash 기반 증분 캐시 부재로, CI에서 `validate` → `index` → `check`를 순차 실행하는 흔한 패턴(`CONTRIBUTING.md`가 권장하는 순서)이 동일 파일을 3번 파싱한다.

**솔루션**: 파일 mtime+size 해시를 키로 하는 프로세스 로컬 캐시(단발성 CLI라 프로세스 간 캐시는 과잉설계)보다, 단일 실행 내에서 파싱 결과를 재사용하는 `functools.lru_cache` 우선 적용:

```python
from functools import lru_cache

@lru_cache(maxsize=None)
def _parse_cached(path_str: str, mtime_ns: int) -> tuple:
    # mtime_ns를 키에 포함해 파일 변경 시 캐시 무효화
    return fm.parse(Path(path_str).read_text(encoding="utf-8"))
```

**테스트 시나리오**:
- 동일 프로세스 내 같은 ADR을 두 커맨드가 참조할 때 파일 읽기 호출 수가 1회로 줄었는지 mock으로 검증
- 파일 수정 후 mtime이 바뀌면 캐시가 무효화되어 새 내용을 반영하는지

#### 3.3 동시성 제어 & 번호 채번 레이스 — 🔴 Critical

**진단**: Top-3 #1과 동일 결함. `identifiers.next_id`와 `commands/exception.py::_next_id` 두 곳 모두 동일한 "glob → max+1" 패턴을 락 없이 반복 구현하고 있어, 여러 병렬 CI 파이프라인(예: 여러 PR이 동시에 `create` 실행)이나 다중 에이전트 세션이 동시에 ADR/Exception을 생성하면 ID 충돌이 발생한다. 현재 테스트 스위트(`test_create.py`)에는 동시성 재현 테스트가 전혀 없다 — `grep` 결과 `fcntl`/`filelock`/`tempfile`/`os.replace` 사용 이력이 코드베이스 전체에서 0건으로 확인됨.

**솔루션**: Top-3 #1의 `adr_directory_lock`을 `exception.py::_next_id`에도 동일 적용 — 두 채번 로직을 `core/identifiers.py`의 공통 `allocate_sequential_id(dir, pattern)` 함수로 통합해 중복 구현 자체를 제거.

**테스트 시나리오**:
- `multiprocessing.Pool`로 `create.run`을 20개 프로세스에서 동시 호출 → 생성된 ADR 번호 20개가 모두 유일한지 검증(현재 코드로는 이 테스트가 확정적으로 실패함)
- 락 보유 중 프로세스를 `SIGKILL`로 강제 종료 후 재실행 시 stale lock으로 데드락에 빠지지 않는지

---

### 2.4 타입 시스템 엄격성 & 런타임 무결성 — 65/100

#### 4.1 Type Variance & 계약 타이핑 — 🟠 High

**진단**: TypeScript 제네릭/유니온 개념은 적용 불가(Python). Python 자체의 타입 힌트도 대부분의 함수 시그니처(`def run(args) -> dict`)에서 `args`가 `argparse.Namespace` 익명 객체라 IDE 자동완성이 사실상 동작하지 않는다. 반환 타입도 `dict`로만 선언되어 있어 `findings[].confidence` 같은 중첩 구조는 코드를 읽기 전까지 알 수 없다. CI 어디에도 `mypy`/`pyright` 게이트가 없다(검색 결과 0건).

**솔루션**: `TypedDict`로 커맨드별 입력/출력 계약을 명시하고 CI에 `mypy --strict` 추가:

```python
# scripts/core/contracts.py
from typing import TypedDict, Literal

class CreateArgs(TypedDict, total=False):
    input: str | None
    interactive: bool
    dir: str
    root: str
    locale: str | None
    slug: str | None
    dry_run: bool

class CheckFinding(TypedDict):
    adr_id: str
    kind: Literal["related", "verified_violation", "review_required", "no_applicable_constraint"]
    confidence: Literal["VERIFIED", "VIOLATED", "UNVERIFIABLE"]
```

**테스트 시나리오**:
- CI에 `mypy skills/adr-toolkit/scripts --strict` 잡 추가 후 baseline 오류 0건 확인
- 16개 커맨드의 `run()` 시그니처를 `TypedDict` 인자로 순차 전환하며 회귀 테스트 통과 확인

#### 4.2 런타임 스키마 검증 — 🟡 Medium

**진단**: ✓ 강점: `core/schema.py`·`core/exceptions.py`가 Zod/Valibot 없이도 실질적인 런타임 구조·타입·정규식 검증을 수행하며, 이는 컴파일 타임 검증이 아예 없는 Python 환경에서 **실제로 강제되는** 유일한 안전망이라 설계 의도가 명확하다. **결함**은 `schemas/adr.schema.json`·`schemas/exception.schema.json`이라는 JSON Schema 파일이 "외부 도구를 위한 문서"로 별도 존재하면서, 런타임 검증기(Python)와 **완전히 독립적으로 손으로 동기화**된다는 점이다(주석에 명시: "this module is the version actually enforced at runtime"). 두 정의가 갈라지는 순간(schema drift) 외부 도구는 통과하는데 실제 런타임은 거부하는 필드가 생길 수 있다.

**솔루션**: JSON Schema를 **단일 진실 소스**로 승격하고 Python 검증기를 그로부터 생성 또는 그것으로 직접 검증하도록 역전:

```python
# core/schema.py 를 jsonschema 라이브러리 기반으로 재작성
import json, jsonschema
from pathlib import Path

_SCHEMA = json.loads((Path(__file__).parents[2] / "schemas" / "adr.schema.json").read_text())

def validate_frontmatter(data: dict) -> list:
    validator = jsonschema.Draft202012Validator(_SCHEMA)
    return [e.message for e in sorted(validator.iter_errors(data), key=str)]
```

**테스트 시나리오**: JSON Schema 파일에 필드를 추가하고 Python 검증기를 갱신하지 **않은** 상태에서 drift 감지 테스트가 실패하는지(현재는 이 테스트 자체가 존재하지 않음 — 신규 작성 필요)

#### 4.3 Defensive Error Architecture — 🟡 Medium

**진단**: ✓ 강점: 도메인별 예외 클래스(`InvalidTransitionError`, `ConfigError`, `ConstraintsError`, `FrontmatterError`, `GitPathsError`)가 실제로 존재하고 각 커맨드가 이를 구조화된 `{code, detail}` JSON으로 변환하는 일관된 패턴을 따른다 — 매직 스트링이지만 최소한 **일관된** 매직 스트링이다. `adr.py:186`의 전역 캐치가 최후 방어선 역할을 하는 것도 견고하다. 결함은 이 5개 예외 클래스가 공통 베이스 클래스를 공유하지 않아 "이 커맨드가 던질 수 있는 예외 전체 목록"을 타입 시스템으로 추적할 수 없다는 것과, 스택 트레이스가 어디에도 보존되지 않는다는 것(§7과 중복 이슈).

**솔루션**: 공통 `AdrToolkitError` 베이스로 통합해 `error_code`를 클래스 속성으로 승격:

```python
class AdrToolkitError(Exception):
    error_code: str = "UNKNOWN_ERROR"
    def to_dict(self) -> dict:
        return {"code": self.error_code, "detail": str(self)}

class InvalidTransitionError(AdrToolkitError):
    error_code = "INVALID_TRANSITION"
```

**테스트 시나리오**: 모든 커맨드의 `except` 절이 `AdrToolkitError`의 서브클래스만 개별 처리하고 나머지는 전역 핸들러로 위임하는지 정적 검사

---

### 2.5 엔터프라이즈 거버넌스 & 컴플라이언스 — 80/100

#### 5.1 ADR 상태 전이 머신 (FSM) — 🟢 Low

**진단**: ✓ 강점: `core/lifecycle.py`는 교과서적인 화이트리스트 FSM이다(`proposed→{accepted,rejected}`, `accepted→{deprecated,superseded}`, 나머지는 종단 상태). `status.py`/`supersede.py` 둘 다 쓰기 전에 반드시 `validate_transition`을 통과해야 하므로 유효하지 않은 전이가 파일에 반영될 경로가 없다. 유일한 아쉬움은 "proposed → deprecated"(합의 없이 제안을 철회) 같은 실무에서 종종 필요한 전이가 빠져 있다는 점 정도다.

**솔루션**: 필요 시 `ALLOWED_TRANSITIONS["proposed"]`에 `"deprecated"`를 추가하는 1줄 변경으로 충분 — 아키텍처 변경 불요.

**테스트 시나리오**: 기존 `test_lifecycle.py`가 이미 전 전이 조합을 파라미터화 테스트 중 — 신규 전이 추가 시 동일 패턴으로 1건 추가

#### 5.2 CI/CD 게이트웨이 & Linter Rules — 🟢 Low

**진단**: ✓ 강점: `check`/`validate` 커맨드가 headless JSON-only CLI로 설계되어 있고 `main()`의 `return 0 if result.get("ok") else 1`이 표준 CI Exit Code 계약을 정확히 지킨다. `constraints:` 블록의 6종 kind(`forbidden_import`, `required_path` 등)는 ArchUnit류 아키텍처 규칙 엔진과 사실상 동등한 표현력을 이미 갖췄다. 다만 이 규칙들이 코드 리뷰를 통과한 `constraints:` YAML 블록 하나에만 의존하므로, 규칙 자체의 오탈자(§2.3의 ReDoS 포함)를 잡는 lint가 CHECK 실행 시점이 아니라 ADR 작성 시점에 있으면 더 좋다.

**솔루션**: `create`/`status` 커맨드 실행 직후 자동으로 새/변경 ADR의 `constraints:` 블록을 파싱해보는 사전 린트를 `validate`에 이미 통합된 흐름과 동일하게 `create.py` 종료 직전에도 실행(현재는 CHECK 실행 시점에야 발견됨).

**테스트 시나리오**: 오탈자 있는 `constraints:`를 포함한 draft로 `create` 실행 시 파일 생성 전에 경고가 뜨는지

#### 5.3 의사결정 계보 추적 (Lineage) — 🟢 Low

**진단**: ✓ 강점: `core/relationships.py::find_cycles`는 `supersedes` 엣지에 대해 정확한 DFS 기반 순환 탐지를 구현하고 있고, `validate.py`가 이를 `SUPERSESSION_CYCLE` 에러로 노출한다. Mermaid(`render_mermaid`)와 순수 SVG(`render_svg`, Node/브라우저 자동화 없이 결정론적 벡터 출력) 두 경로 모두 그래프 시각화를 지원하는 것은 이 규모의 도구치고 이례적으로 잘 갖춰진 기능이다. `supersession_mismatches`가 양방향 링크 불일치(A는 B를 supersede한다는데 B는 A에 의해 superseded 되었다고 안 적힌 경우)까지 잡아낸다.

**솔루션**: 이미 우수. 유일한 개선점은 `render_mermaid`는 title을 이스케이프하는데 `index.py`의 README 렌더러는 안 하는 §2.3의 비일관성 — 공통 `safe_md_link_text` 헬퍼로 통일.

**테스트 시나리오**: 3-ADR 순환(A supersedes B, B supersedes C, C supersedes A) 픽스처로 `find_cycles`가 정확히 `(A,B,C)` 튜플 1개를 반환하는지(기존 `test_relationships.py` 커버리지 확인됨)

---

### 2.6 개발자 경험(DX) & 툴링 인체공학 — 78/100

#### 6.1 설정 복잡도 최소화 — 🟢 Low

**진단**: ✓ 강점: `.adr-toolkit.json`(schema_version + locale) 하나로 시작해, `core/config.py::resolve_locale`이 `CLI 인자 → draft 값 → 저장소 설정 → 기본값` 순서의 명확한 cascading을 구현한다. Zero-config(`init` 한 줄)에서 8개 로케일 커스터마이징까지 계단식으로 확장되는 설계가 실제로 동작한다. `ALLOWED_KEYS` 화이트리스트가 알 수 없는 설정 키를 명시적으로 거부하는 것도 좋은 습관(조용한 오타 허용 방지).

**솔루션**: 현재 설정 항목이 2개뿐이라 과설계 위험이 더 크다 — 추가 조치 불요, 항목이 늘어날 때(예: CHECK 규칙 severity 임계값) 동일 cascading 패턴을 재사용할 것.

**테스트 시나리오**: 기존 `test_config.py`가 우선순위 4단계를 이미 개별 테스트 중 — 신규 설정 키 추가 시 동일 매트릭스 확장

#### 6.2 CLI 인터랙션 & 가독성 — 🟡 Medium

**진단**: 모든 커맨드가 `--json`이 강제된 기계 친화적 출력이라는 점은 명확한 설계 선택이다(사람이 아니라 에이전트가 1차 소비자). `create --interactive`가 에이전트 없이도 터미널에서 직접 인터뷰를 진행하는 폴백을 제공하는 것도 실용적이다. 반면 **사람**이 직접 CLI를 두드릴 때를 위한 배려는 약하다: 색상 강조, 진행 표시줄, `--quiet`(현재는 JSON이 유일 출력이라 quiet 자체가 무의미), TTY 감지 분기가 전무하다.

**솔루션**: TTY 감지 시에만 최소한의 사람용 요약 라인을 stderr에 추가(stdout 계약은 불변 유지):

```python
if sys.stderr.isatty() and not os.environ.get("ADR_TOOLKIT_NO_COLOR"):
    print(f"\033[2m→ {args.operation} {'ok' if result.get('ok') else 'FAILED'}\033[0m", file=sys.stderr)
```

**테스트 시나리오**: stdout이 파이프로 리다이렉트된 상태(`isatty()==False`)에서 stderr에 추가 출력이 전혀 없는지(기존 소비자 회귀 방지)

#### 6.3 스캐폴딩 및 플러그인 SDK — 🟠 High

**진단**: 새 AI 하네스를 위한 어댑터를 만들려는 사람에게 제공되는 것은 `adapters/generic/README.md` 한 장뿐이다 — 공식 SDK, 매니페스트 스캐폴딩 CLI, Mock Context 테스트 킷이 없다. 4개 기존 어댑터(Claude/Codex/Gemini/Antigravity)가 사실상의 참고 구현 역할을 하고는 있지만, 신규 기여자는 4개 매니페스트 형식을 손으로 비교하며 5번째를 작성해야 한다. `tests/unit/test_*_adapter.py` 4종이 각 매니페스트의 구조를 검증하는 건 좋지만, 이 자체가 "SDK 부재"의 방증이다(테스트가 매번 새로 작성되지, 공유 검증기가 없음).

**솔루션**: 공통 어댑터 매니페스트 검증기를 추출해 신규 어댑터 작성자가 재사용하도록 공개:

```python
# scripts/adapter_sdk.py
def validate_adapter_manifest(manifest: dict, *, required_fields=("name","version","description")) -> list:
    return [f"missing {f}" for f in required_fields if f not in manifest]

# adapters/README.md 에 "5번째 하네스 추가하기" 튜토리얼 + 이 검증기 사용법 추가
```

**테스트 시나리오**: 4개 기존 매니페스트가 신규 `validate_adapter_manifest`를 통과하는지(기존 4개 테스트를 이 공유 함수 호출로 리팩터링)

---

### 2.7 관측 가능성 & 원격 측정 — 25/100

#### 7.1 구조화된 로깅 — 🔴 Critical

**진단**: Top-3 #3과 동일. `logging` 모듈 import 자체가 코드베이스 전체에서 0건(`grep -rn "import logging"` 결과 없음). 모든 진단 정보는 최종 JSON 응답의 `warnings`/`errors` 배열뿐이며, 이는 "결과 보고"이지 "실행 과정 로그"가 아니다. 상관관계 ID, 로그 레벨 세분화, JSON 구조화 로그 모두 부재.

**솔루션**: Top-3 #3의 `telemetry.py` 참조.

**테스트 시나리오**: `ADR_TOOLKIT_LOG_LEVEL=debug` 설정 시 stderr에 JSON Lines 로그가 나오고 stdout은 순수 결과 JSON만 유지되는지

#### 7.2 프로파일링 & 진단 모드 — 🟠 High

**진단**: 실행 시간 측정, 병목 리포트, 메모리 프로파일링 커맨드 모두 없음. §3의 확장성 주장(느리다/안 느리다)조차 현재는 측정 도구가 없어 **검증 불가능한 주장**이다 — 이 항목의 부재가 §3 진단의 신뢰도 자체를 낮춘다.

**솔루션**: `adr.py::main`에 선택적 타이밍 계측을 추가하고 `--diagnostic` 플래그로 노출:

```python
start = time.perf_counter()
result = HANDLERS[args.operation](args)
if getattr(args, "diagnostic", False):
    result["_diagnostics"] = {"elapsed_ms": round((time.perf_counter()-start)*1000, 1)}
```

**테스트 시나리오**: ADR 100/1,000/2,000개 픽스처에서 `--diagnostic` 출력의 `elapsed_ms`를 CI 아티팩트로 기록해 회귀 추세를 추적

---

### 2.8 테스트 완전성 & 릴리스 엔지니어링 — 82/100

#### 8.1 테스트 피라미드 구성 — 🟡 Medium

**진단**: ✓ 강점: 유닛 42개 + 통합 7개 파일, 약 5,200줄의 테스트 코드가 `tmp_path` 기반 **실제 파일시스템**에서 동작하는 진짜 E2E에 가깝다(모킹 남용 없음). `harness-parity` CI 잡은 실제 Codex/Gemini CLI를 설치해 어댑터를 검증하는, 이 규모 오픈소스에서는 보기 드문 수준의 통합 테스트다. **결함**: `pytest-cov`/coverage 측정 자체가 CI 어디에도 없다 — "Branch 90%+"라는 목표를 애초에 **측정할 수 없다**. 커버리지 수치가 없으므로 실제 커버리지가 90%든 60%든 현재는 아무도 모른다.

**솔루션**:

```yaml
# .github/workflows/test.yml 에 추가
- run: pip install pytest pytest-cov
- run: python -m pytest tests/unit tests/integration --cov=scripts --cov-branch --cov-fail-under=85 --cov-report=xml
```

**테스트 시나리오**: coverage 도입 직후 baseline 측정 → 85% 미만 모듈 식별 → 우선순위화된 보강 목록 작성

#### 8.2 카오스 & 엣지 케이스 복원력 — 🟠 High

**진단**: ✓ 강점: 손상된 프론트매터, 깨진 링크, 순환 참조, 만료된 예외 등 "문서가 잘못됐을 때"의 우아한 성능 저하(graceful degradation)는 `check.py`·`index.py`·`locale.py` 전반에 걸쳐 의도적으로 잘 설계되어 있다(예: 로케일 파일 파싱 실패 시 크래시 대신 조용히 fallback). **결함**: "플러그인이 무한 루프에 빠지거나 크래시"라는 원 질문은 실행되는 플러그인이 없으므로 성립하지 않지만, 실제 대응 개념인 "프로세스가 쓰기 도중 죽었을 때"의 복원력은 Top-3 #1에서 지적한 대로 전무하다 — 이것이 진짜 카오스 시나리오다.

**솔루션**: Top-3 #1 적용 후, kill -9 카오스 테스트를 테스트 스위트에 추가.

**테스트 시나리오**: `os.fork()` 후 자식 프로세스가 `atomic_write_text` 중간에 `os.kill(pid, SIGKILL)`로 강제 종료됐을 때, 부모가 확인하는 ADR 파일이 항상 파싱 가능한(이전 또는 이후) 유효 상태인지

#### 8.3 Cross-Platform & 런타임 호환성 — 🟢 Low

**진단**: ✓ 강점: CI 매트릭스가 `ubuntu-latest / macos-latest / windows-latest` × `Python 3.9 / 3.12`를 실제로 돌린다(`test.yml` 확인) — 이는 요청서가 요구한 항목을 이미 충족하는 몇 안 되는 사례다. `git_paths.py`가 `core.quotePath=false`로 비-ASCII 경로를, `-z`로 개행 포함 파일명을 안전 처리한다. Node/Deno/Bun 다중 런타임 지원은 해당 사항 없음(Python 전용 도구). 유일한 갭은 Windows에서 `fcntl` 기반 락(Top-3 #1 해결책)이 그대로 동작하지 않는다는 점 — 이미 `msvcrt` 분기로 코드 예시에 반영함.

**솔루션**: 추가 조치 불요. Top-3 #1의 잠금 구현이 Windows/POSIX 양쪽을 이미 분기 처리했는지 CI 매트릭스로 재확인.

**테스트 시나리오**: Windows 러너에서 신규 `adr_directory_lock`으로 동시 `create` 20회 실행 후 ID 유일성 검증(기존 3-OS 매트릭스에 자동 편입됨)

#### 8.4 오픈소스 기여 거버넌스 — 🟢 Low

**진단**: ✓ 강점: `CONTRIBUTING.md`·`CODE_OF_CONDUCT.md`·`SECURITY.md` 3종 모두 구비되어 있고, `SECURITY.md`의 "Scope"가 "path handling", "release workflow", "plugin manifest" 등 실제 코드 위협 표면과 정확히 일치하게 작성되어 있어 형식적 문서가 아니다. Git Flow(`develop`/`master`/`release/*`)와 태그 기반 릴리스가 `AGENTS.md`에 명문화되고 `release.yml`이 태그-VERSION 일치를 강제한다. 다만 Semantic Commit 강제(commitlint 등)나 Changesets/semantic-release 같은 **자동 버전 산정**은 없다 — 버전은 인간이 수동으로 올린다(문서에 "No auto version bump"로 명시된 의도적 선택).

**솔루션**: 수동 버전 관리가 이 규모에서는 합리적 선택이므로 강제 도입 비권장. 다만 PR 제목에 Conventional Commits 형식을 요구하는 경량 CI 체크(예: `amannn/action-semantic-pull-request`) 정도는 비용 대비 효과가 높음.

**테스트 시나리오**: PR 제목이 `feat:`/`fix:`/`docs:` 접두어 없이 열렸을 때 체크가 실패하는지

---

## 3. 우선순위 로드맵

24개 항목을 리스크 레벨과 착수 난이도로 재정렬한 실행 순서.

| 순서 | 항목 | 리스크 | 왜 이 순서인가 |
|---|---|---|---|
| 1주차 | 3.3 / Top-3 #1 — 원자적 쓰기 + ID 락 | 🔴 Critical | 데이터 무결성은 다른 모든 기능의 전제조건. 신규 모듈 1개(`atomic_io.py`)로 5개 커맨드에 즉시 적용 가능. |
| 1주차 | 2.3 / Top-3 #2 — Markdown 이스케이프 + ReDoS 가드 | 🔴 Critical | 기존 `_mermaid_label` 패턴을 재사용만 하면 되는 낮은 난이도 대비 높은 임팩트. |
| 2주차 | 7.1 / Top-3 #3 — 구조화 로깅 | 🔴 Critical | 이후 모든 항목의 디버깅 가능성을 좌우 — 조기 도입할수록 나머지 작업의 비용이 줄어든다. |
| 2주차 | 8.1 — 커버리지 측정 도입 | 🟠 High | CI 설정 한 줄. 이후 리팩터링(§1.3, §4.1)의 안전망이 된다. |
| 3주차 | 1.3 — 출력 계약 스키마 고정 | 🟠 High | 4.2의 JSON Schema 단일화와 작업을 공유할 수 있어 묶어서 진행. |
| 3주차 | 4.2 — JSON Schema를 단일 진실 소스로 역전 | 🟡 Medium | 1.3과 동일 파일을 다루므로 순차 진행이 자연스러움. |
| 4주차 | 2.2 — 릴리스 아티팩트 체크섬/서명 | 🟠 High | 릴리스 워크플로 변경은 배포본이 늘어나기 전(현재 v0.2.0)에 도입하는 편이 마이그레이션 비용이 낮음. |
| 백로그 | 6.3 — 어댑터 SDK 추출 | 🟠 High | 5번째 하네스 요청이 실제로 들어오는 시점까지 지연 가능(YAGNI). |
| 백로그 | 4.1 — mypy 전면 도입 | 🟠 High | 점진적 도입 가능하나 전체 적용은 공수가 커 커버리지 안전망(8.1) 확보 후 진행. |

---

## 방법론 한계

본 감사는 정적 코드 검토와 CI 설정 분석에 기반하며, 런타임 부하 테스트나 실제 침투 테스트는 수행하지 않았다. 점수는 감사자의 판단이 반영된 정성 평가이며, 정량 지표(커버리지 %, 응답 시간 ms)는 §7.2/§8.1에서 지적한 대로 현재 도구 자체에 계측이 없어 다수 항목에서 "측정 불가"를 "가정된 안전"으로 대체하지 않고 명시적으로 리스크로 처리했다.
