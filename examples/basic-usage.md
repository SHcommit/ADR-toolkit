# Example: Basic Usage (INIT → RECORD → INDEX)

## Scenario

A team initializing ADR management in a repository needs to scaffold `docs/decisions/`, evaluate whether adopting PostgreSQL for persistence requires an architectural decision record, record `ADR-0002` with standard metadata, and generate a searchable decision index for the team.

## Input

```bash
# 1. Verify if an ADR directory already exists
python skills/adr-toolkit/scripts/adr.py preflight --json

# 2. Scaffold docs/decisions/ directory and ADR-0001
python skills/adr-toolkit/scripts/adr.py init --dir docs/decisions --json

# 3. Check for existing ADRs covering database persistence
python skills/adr-toolkit/scripts/adr.py related \
  --paths src/db/ --tags database persistence --dir docs/decisions --json

# 4. Evaluate decision significance against architectural criteria
python skills/adr-toolkit/scripts/adr.py significance --input scores.json --json

# 5. Create ADR-0002 from approved draft
python skills/adr-toolkit/scripts/adr.py create --input draft.json --dir docs/decisions --json

# 6. Validate directory schema and regenerate index
python skills/adr-toolkit/scripts/adr.py validate --dir docs/decisions --json
python skills/adr-toolkit/scripts/adr.py index --dir docs/decisions --json
```

## What Happens

1. `preflight` verifies that no existing ADR directory exists in the target repository.
2. `init` scaffolds `.adr-toolkit.json`, `docs/decisions/`, template `adr-template.md`, and `0001-record-architecture-decisions.md`.
3. `related` scans existing decision metadata to ensure no conflicting ADR already governs `src/db/`.
4. `significance` evaluates the decision matrix score (threshold score $\ge 6$ classifies as `recommended`).
5. `create` assigns ID `ADR-0002`, validates schema, and writes `docs/decisions/0002-use-postgresql-for-persistence.md`.
6. `index` generates `docs/decisions/README.md` organized by status and tag.

## Output

### 1. Significance Output

```json
{
  "ok": true,
  "operation": "significance",
  "total": 12,
  "classification": "recommended",
  "warnings": []
}
```

### 2. Created ADR Output

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

### 3. Generated Decision Index (`docs/decisions/README.md`)

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
