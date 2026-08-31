# Example: Mechanical Constraint Enforcement (RECORD WITH CONSTRAINTS → CHECK → RESOLVE)

## Scenario

An architecture decision records an explicit constraint forbidding MongoDB drivers in `src/db/**`. When a developer accidentally imports `mongodb` into `src/db/connection.js`, `check --uncommitted` flags a `VIOLATED` finding. The team can resolve it either by refactoring the code to `pg` (restoring `VERIFIED` status) or by registering a time-bound exception.

## Input

### 1. ADR Implementation Constraint (YAML in `ADR-0002`)

```yaml
constraints:
  - id: no-mongodb-driver
    kind: forbidden_import
    paths: ["src/db/**"]
    pattern: ["mongodb", "mongoose"]
    severity: major
    message: "This service uses PostgreSQL for persistence — do not import MongoDB driver."
```

### 2. Checking Uncommitted Diff

```bash
# Check code diff against active ADR constraints
python skills/adr-toolkit/scripts/adr.py check --uncommitted --dir docs/decisions --json
```

### 3. Registering an Exception (Optional Resolution)

```bash
# Register temporary exception for migration script
python skills/adr-toolkit/scripts/adr.py exception --input exception.json --dir docs/decisions --json
```

## What Happens

1. `check --uncommitted` inspects modified files in the working directory against active `constraints:` in Accepted ADRs.
2. When `src/db/connection.js` contains `require("mongodb")`, `check` produces a `verified_violation` finding with `confidence: "VIOLATED"`.
3. `check` never automatically modifies code — it returns 5 resolution options (`fix_code`, `supersede_adr`, `adjust_scope`, `register_exception`, `false_positive`).
4. If `register_exception` is selected, `exception` validates schema and writes a deterministic `EXC-0001` record under `docs/decisions/exceptions/0001.json`.
5. Once code is refactored to `pg`, re-running `check` returns `confidence: "VERIFIED"`.

## Output

### 1. Violation Finding Output (`confidence: "VIOLATED"`)

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
      "message": "This service uses PostgreSQL for persistence — do not import MongoDB driver.",
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

### 2. Registered Exception Output (`EXC-0001`)

```json
{
  "ok": true,
  "operation": "exception",
  "created": "docs/decisions/exceptions/0001.json",
  "id": "EXC-0001",
  "warnings": []
}
```

### 3. Fixed Check Output (`confidence: "VERIFIED"`)

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
