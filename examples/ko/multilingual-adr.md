# 예시: 다국어 저장소 지원 (`--locale ko` 및 ASCII 슬러그 `--slug`)

## 시나리오 (Scenario)

한국어 엔지니어링 팀이 한국어(`ko`)로 아키텍처 결정서의 제목과 본문을 작성하면서도, 다양한 OS 환경 및 Git 호환성을 유지하기 위해 기계 안정적 JSON 계약, 표준 MADR 헤딩, 이식성 있는 ASCII 파일명을 유지하고자 합니다.

## 입력 (Input)

```bash
# 1. 한국어 기본 로케일로 ADR 디렉터리 초기화
python skills/adr-toolkit/scripts/adr.py init --locale ko --dir docs/decisions --json

# 2. 한국어 제목과 본문으로 ADR을 작성하고 승인된 ASCII 슬러그 전달
python skills/adr-toolkit/scripts/adr.py create \
  --input draft_ko.json \
  --slug event-driven-payment-architecture \
  --dir docs/decisions \
  --json

# 3. 한국어 지원 색인 생성
python skills/adr-toolkit/scripts/adr.py index --dir docs/decisions --json
```

## 동작 방식 (What Happens)

1. `init --locale ko` 명령이 저장소 루트의 `.adr-toolkit.json` 파일에 `"locale": "ko"` 기본 설정을 지정합니다.
2. `create` 명령이 한국어 제목(`결제 서비스 이벤트 기반 아키텍처 도입`)이 포함된 드래프트를 읽고, 전달받은 의미 있는 ASCII 슬러그(`event-driven-payment-architecture`)를 검증하여 `docs/decisions/0002-event-driven-payment-architecture.md` 파일명으로 안전하게 작성합니다.
3. `index` 명령이 `.adr-toolkit.json` 기본 로케일을 읽어 `docs/decisions/README.md` 내에 한국어 헤더(`# 결정 기록`, `## 상태별`, `## 태그별`)를 렌더링합니다.
4. 필드 키, ID (`ADR-0002`), 상태 값 (`accepted`), 파일명 등 시스템 계약은 ASCII로 유지됩니다.

## 출력 결과 (Output)

### 1. 저장소 구성 파일 (`.adr-toolkit.json`)

```json
{
  "schema_version": 1,
  "locale": "ko"
}
```

### 2. 생성된 한국어 ADR 출력 (`create`)

```json
{
  "ok": true,
  "operation": "create",
  "dry_run": false,
  "created": "docs/decisions/0002-event-driven-payment-architecture.md",
  "id": "ADR-0002",
  "warnings": []
}
```

### 3. 생성된 한국어 의사결정 색인 (`docs/decisions/README.md`)

```markdown
# 결정 기록

## 상태별

### 채택됨 (Accepted)
- [ADR-0001 — Record architecture decisions](0001-record-architecture-decisions.md)
- [ADR-0002 — 결제 서비스 이벤트 기반 아키텍처 도입](0002-event-driven-payment-architecture.md)

## 태그별

### payment
- [ADR-0002 — 결제 서비스 이벤트 기반 아키텍처 도입](0002-event-driven-payment-architecture.md)
```
