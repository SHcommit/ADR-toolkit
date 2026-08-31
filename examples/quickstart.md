# Quickstart: INIT → RECORD → CHECK

This walks through the three core operations against a small example
service, from an empty repo to CHECK catching a real rule violation. Every
command and JSON block below is real output from actually running these
commands — nothing here is hypothetical.

All commands assume `skills/adr-toolkit/` is on your path somehow (see the
root [README](../README.md) for per-harness install, or just call the
script directly as shown here: `python skills/adr-toolkit/scripts/adr.py`).

## Setup

A tiny Node service with no ADRs yet:

```text
example-service/
├── package.json
└── src/db/connection.js
```

## 1. INIT — scaffold the ADR directory

```bash
python skills/adr-toolkit/scripts/adr.py preflight --json
```

```json
{
  "ok": true,
  "operation": "preflight",
  "python_version": "3.9.6",
  "git_available": true,
  "existing_adr_directory": null,
  "warnings": [],
  "errors": []
}
```

`existing_adr_directory` is `null`, so it's safe to scaffold:

```bash
python skills/adr-toolkit/scripts/adr.py init --dir docs/decisions --json
```

```json
{
  "ok": true,
  "operation": "init",
  "dry_run": false,
  "created": [
    ".adr-toolkit.json",
    "docs/decisions",
    "docs/decisions/adr-template.md",
    "docs/decisions/0001-record-architecture-decisions.md"
  ]
}
```

## 2. RECORD — capture a decision with a checkable rule

Before drafting, check for anything already covering this area:

```bash
python skills/adr-toolkit/scripts/adr.py related \
  --paths src/db/ --tags database persistence --dir docs/decisions --json
```

```json
{"ok": true, "operation": "related", "count": 0, "matches": [], "warnings": []}
```

Nothing exists yet. Score the decision's significance against the seven
criteria (`references/significance-rules.md` explains each one) and check
whether it clears the bar for recording at all:

```bash
python skills/adr-toolkit/scripts/adr.py significance --input scores.json --json
```

```json
{"ok": true, "operation": "significance", "total": 12, "classification": "recommended"}
```

`recommended` — draft it. This decision also gets a structured
`constraints:` block in its Implementation Constraints section, so CHECK
can enforce it mechanically later, not just document it in prose:

````markdown
## Implementation Constraints

```yaml
constraints:
  - id: no-mongodb-driver
    kind: forbidden_import
    paths: ["src/db/**"]
    pattern: ["mongodb", "mongoose"]
    severity: major
    message: "This service uses PostgreSQL for persistence (see this ADR) — do not add a MongoDB driver."
```
````

Write the full draft (title, body, tags, `affected_paths`) to a JSON file
and create it:

```bash
python skills/adr-toolkit/scripts/adr.py create --input draft.json --dir docs/decisions --json
```

```json
{
  "ok": true,
  "operation": "create",
  "dry_run": false,
  "created": "docs/decisions/0002-use-postgresql-for-persistence.md",
  "id": "ADR-0002"
}
```

Then validate and regenerate the index:

```bash
python skills/adr-toolkit/scripts/adr.py validate --dir docs/decisions --json
python skills/adr-toolkit/scripts/adr.py index --dir docs/decisions --json
```

Both report `"ok": true`, and `docs/decisions/README.md` now reads:

```markdown
# Decision Log

## By status

### Accepted
- [ADR-0001 — Record architecture decisions](0001-record-architecture-decisions.md)
- [ADR-0002 — Use PostgreSQL for persistence](0002-use-postgresql-for-persistence.md)

## By tag

### database
- [ADR-0002 — Use PostgreSQL for persistence](0002-use-postgresql-for-persistence.md)
...
```

## 3. CHECK — catch a real violation

Commit the ADR, then a developer (unaware of it) adds a MongoDB driver:

```js
// src/db/connection.js
const mongodb = require("mongodb");

module.exports = { connect: () => mongodb.connect(process.env.DB_URL) };
```

```bash
python skills/adr-toolkit/scripts/adr.py check --uncommitted --dir docs/decisions --json
```

```json
{
  "ok": true,
  "operation": "check",
  "diff": {"mode": "uncommitted", "ref": null, "files_changed": 1},
  "findings": [
    {
      "rule_id": "no-mongodb-driver",
      "kind": "verified_violation",
      "severity": "major",
      "message": "This service uses PostgreSQL for persistence (see this ADR) — do not add a MongoDB driver.",
      "file": "src/db/connection.js",
      "evidence": {"line": "const mongodb = require(\"mongodb\");", "pattern": "mongodb"},
      "adr_id": "ADR-0002",
      "resolutions": ["fix_code", "supersede_adr", "adjust_scope", "register_exception", "false_positive"],
      "confidence": "VIOLATED"
    }
  ],
  "warnings": []
}
```

CHECK never picks a resolution for you — it always hands back all five and
lets a human decide. Here the developer picks `fix_code`:

```js
// src/db/connection.js
const { Pool } = require("pg");

module.exports = { pool: new Pool({ connectionString: process.env.DB_URL }) };
```

```bash
python skills/adr-toolkit/scripts/adr.py check --uncommitted --dir docs/decisions --json
```

```json
{
  "ok": true,
  "operation": "check",
  "diff": {"mode": "uncommitted", "ref": null, "files_changed": 1},
  "findings": [{"adr_id": "ADR-0002", "kind": "related", "confidence": "VERIFIED"}],
  "warnings": []
}
```

The violation is gone — `related` means the diff still touches a path this
ADR governs, but the explicit structural rule that fired before no longer
does. It is `VERIFIED` only for that rule and selected diff, not proof of the
entire architecture.

## Multilingual variation — Korean repository, portable filename

In a fresh repository, choose Korean once during INIT:

```bash
python skills/adr-toolkit/scripts/adr.py init --locale ko --dir docs/decisions --json
```

Real output:

```json
{
  "ok": true,
  "operation": "init",
  "dry_run": false,
  "created": [
    ".adr-toolkit.json",
    "docs/decisions",
    "docs/decisions/adr-template.md",
    "docs/decisions/0001-record-architecture-decisions.md"
  ]
}
```

The config now supplies `ko` to CREATE and INDEX. Given a reviewed draft whose
title is `결제 시스템 분리`, let the agent propose `separate-payment-system`
and approve that semantic ASCII slug before mutation:

```bash
python skills/adr-toolkit/scripts/adr.py create --input draft.json \
  --slug separate-payment-system --dir docs/decisions --json
```

Real output:

```json
{
  "ok": true,
  "operation": "create",
  "dry_run": false,
  "created": "docs/decisions/0002-separate-payment-system.md",
  "id": "ADR-0002"
}
```

The title/body remain Korean and the ADR records `locale: ko`; the core never
translates the title to obtain the filename. Omitting an approved slug for a
title with no ASCII characters safely uses `decision` instead.

```bash
python skills/adr-toolkit/scripts/adr.py index --dir docs/decisions --json
```

The real command reports `"count": 2`, and the generated index begins with
`# 결정 기록` because it reads the repository default.

## Next steps

- `--since <ref>` and `--staged` are the other two `check`/`diff` range
  modes, for a branch/commit range or a staged-changes review — see
  `SKILL.md`'s CHECK section.
- `references/conflict-rules.md` documents all six `constraints:` rule
  kinds (`forbidden_import` was the only one used here) and the four-way
  finding classification plus VERIFIED / VIOLATED / UNVERIFIABLE /
  NOT_APPLICABLE confidence meaning in full.
- No AI harness at all? `create --interactive` runs the same interview in
  a plain terminal — see the root [README](../README.md).
