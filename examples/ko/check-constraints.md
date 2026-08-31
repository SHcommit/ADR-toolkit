# 예시: 기계적 제약조건 검증 (RECORD WITH CONSTRAINTS → CHECK → RESOLVE)

## 시나리오 (Scenario)

ADR에 `src/db/**` 경로 내에서 MongoDB 드라이버 사용을 금지하는 제약조건(`forbidden_import`)을 명시했습니다. 다른 개발자가 실수로 `src/db/connection.js` 파일에 `require("mongodb")` 코드를 작성하고 커밋하지 않은 상태에서 `check --uncommitted`를 실행하면 `VIOLATED` 위반이 감지됩니다. 개발자는 코드를 PostgreSQL 드라이버(`pg`)로 수정하여 `VERIFIED` 상태로 복구하거나, 기한이 정해진 예외(`exception`)를 등록하여 해결할 수 있습니다.

## 입력 (Input)

### 1. ADR 내 명시된 제약조건 규칙 (YAML)

```yaml
constraints:
  - id: no-mongodb-driver
    kind: forbidden_import
    paths: ["src/db/**"]
    pattern: ["mongodb", "mongoose"]
    severity: major
    message: "이 서비스는 데이터 저장을 위해 PostgreSQL을 사용합니다. MongoDB 드라이버를 추가하지 마세요."
```

### 2. 커밋되지 않은 코드 diff 검사

```bash
# 작업 트리의 변경 사항을 활성화된 ADR 제약조건과 비교 검사
python skills/adr-toolkit/scripts/adr.py check --uncommitted --dir docs/decisions --json
```

### 3. 일시적 예외 등록 (해결 옵션 중 하나)

```bash
# 마이그레이션 스크립트를 위한 일시적 예외 등록
python skills/adr-toolkit/scripts/adr.py exception --input exception.json --dir docs/decisions --json
```

## 동작 방식 (What Happens)

1. `check --uncommitted` 명령이 작업 트리의 변경된 소스 코드를 채택된(Accepted) ADR의 `constraints:` 구문과 비교 검사합니다.
2. `src/db/connection.js`에 `require("mongodb")` 구문이 존재하면, `check` 명령은 `confidence: "VIOLATED"` 상태의 `verified_violation` 결과를 반환합니다.
3. `check`는 스스로 코드를 수정하지 않으며, 사용자에게 5가지 해결 방법(`fix_code`, `supersede_adr`, `adjust_scope`, `register_exception`, `false_positive`)을 안내합니다.
4. `register_exception`을 선택하면 `exception` 명령이 스키마를 검증하고 `docs/decisions/exceptions/0001.json` 위치에 deterministic 예외 기록(`EXC-0001`)을 생성합니다.
5. 코드를 `pg`로 리팩토링한 후 `check`를 다시 실행하면 `confidence: "VERIFIED"`로 통과합니다.

## 출력 결과 (Output)

### 1. 규칙 위반 감지 결과 (`confidence: "VIOLATED"`)

```json
{
  "ok": true,
  "operation": "check",
  "diff": {
    "mode": "uncommitted",
    "ref": null,
    "files_changed": 1
  },
  "findings": [
    {
      "rule_id": "no-mongodb-driver",
      "kind": "verified_violation",
      "severity": "major",
      "message": "이 서비스는 데이터 저장을 위해 PostgreSQL을 사용합니다. MongoDB 드라이버를 추가하지 마세요.",
      "file": "src/db/connection.js",
      "evidence": {
        "line": "const mongodb = require(\"mongodb\");",
        "pattern": "mongodb"
      },
      "adr_id": "ADR-0002",
      "resolutions": [
        "fix_code",
        "supersede_adr",
        "adjust_scope",
        "register_exception",
        "false_positive"
      ],
      "confidence": "VIOLATED"
    }
  ],
  "warnings": []
}
```

### 2. 예외 등록 결과 (`EXC-0001`)

```json
{
  "ok": true,
  "operation": "exception",
  "created": "docs/decisions/exceptions/0001.json",
  "id": "EXC-0001",
  "warnings": []
}
```

### 3. 코드 수정 후 검사 통과 결과 (`confidence: "VERIFIED"`)

```json
{
  "ok": true,
  "operation": "check",
  "diff": {
    "mode": "uncommitted",
    "ref": null,
    "files_changed": 1
  },
  "findings": [
    {
      "adr_id": "ADR-0002",
      "kind": "related",
      "confidence": "VERIFIED"
    }
  ],
  "warnings": []
}
```
