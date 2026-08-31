# 예시: 기본 사용법 (INIT → RECORD → INDEX)

## 시나리오 (Scenario)

프로젝트에 ADR 관리를 처음 도입하려는 팀이 있습니다. 이 팀은 `docs/decisions/` 디렉터리를 초기화하고, 영동적 데이터 저장을 위해 PostgreSQL 도입을 결정했습니다. 해당 결정이 아키텍처 기록 대상인지 평가(`significance`)한 후 `ADR-0002`를 기록하고, 팀원을 위한 의사결정 색인 문서(Index)를 자동 생성합니다.

## 입력 (Input)

```bash
# 1. 기존 ADR 디렉터리 존재 여부 확인
python skills/adr-toolkit/scripts/adr.py preflight --json

# 2. docs/decisions/ 디렉터리 및 ADR-0001 초기 생성
python skills/adr-toolkit/scripts/adr.py init --dir docs/decisions --json

# 3. 데이터베이스/지속성 관련 기존 ADR 중복 여부 확인
python skills/adr-toolkit/scripts/adr.py related \
  --paths src/db/ --tags database persistence --dir docs/decisions --json

# 4. 아키텍처 항목 기준 평가 (Significance Scoring)
python skills/adr-toolkit/scripts/adr.py significance --input scores.json --json

# 5. 검토 완료된 드래프트로부터 ADR-0002 생성
python skills/adr-toolkit/scripts/adr.py create --input draft.json --dir docs/decisions --json

# 6. 스키마 검증 및 색인(README.md) 재생성
python skills/adr-toolkit/scripts/adr.py validate --dir docs/decisions --json
python skills/adr-toolkit/scripts/adr.py index --dir docs/decisions --json
```

## 동작 방식 (What Happens)

1. `preflight` 명령이 저장소 내 기존 ADR 디렉터리 존재 여부를 검증합니다.
2. `init` 명령이 `.adr-toolkit.json`, `docs/decisions/`, `adr-template.md` 및 `0001-record-architecture-decisions.md`를 생성합니다.
3. `related` 명령이 기존 ADR 메타데이터를 검색하여 `src/db/` 관련 충돌 문서가 없는지 확인합니다.
4. `significance` 명령이 점수를 계산하여 기록 권장 여부(점수합계 $\ge 6$ 시 `recommended`)를 판정합니다.
5. `create` 명령이 `ADR-0002` ID를 할당하고 스키마를 검증한 후 `docs/decisions/0002-use-postgresql-for-persistence.md` 파일을 생성합니다.
6. `index` 명령이 상태별/태그별로 정리된 `docs/decisions/README.md` 색인 문서를 자동 생성합니다.

## 출력 결과 (Output)

### 1. 중요도 평가 결과 (`significance`)

```json
{
  "ok": true,
  "operation": "significance",
  "total": 12,
  "classification": "recommended",
  "warnings": []
}
```

### 2. 생성된 ADR 결과 (`create`)

```json
{
  "ok": true,
  "operation": "create",
  "dry_run": false,
  "created": "docs/decisions/0002-use-postgresql-for-persistence.md",
  "id": "ADR-0002",
  "warnings": []
}
```

### 3. 생성된 의사결정 색인 (`docs/decisions/README.md`)

```markdown
# Decision Log

## By status

### Accepted
- [ADR-0001 — Record architecture decisions](0001-record-architecture-decisions.md)
- [ADR-0002 — Use PostgreSQL for persistence](0002-use-postgresql-for-persistence.md)

## By tag

### database
- [ADR-0002 — Use PostgreSQL for persistence](0002-use-postgresql-for-persistence.md)

### persistence
- [ADR-0002 — Use PostgreSQL for persistence](0002-use-postgresql-for-persistence.md)
```
