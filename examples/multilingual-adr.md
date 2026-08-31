# Example: Multilingual Repository Support (`--locale ko` & ASCII Slug `--slug`)

## Scenario

A global or non-English software engineering team wants to write architecture decision titles and bodies in their native language (e.g. Korean `ko`) while maintaining machine-stable JSON contracts, standard MADR structure headings, and portable ASCII filenames for Git and filesystem compatibility across different operating systems.

## Input

```bash
# 1. Initialize ADR directory with Korean locale default
python skills/adr-toolkit/scripts/adr.py init --locale ko --dir docs/decisions --json

# 2. Create ADR with Korean title & body, passing an approved ASCII slug
python skills/adr-toolkit/scripts/adr.py create \
  --input draft_ko.json \
  --slug event-driven-payment-architecture \
  --dir docs/decisions \
  --json

# 3. Generate localized index
python skills/adr-toolkit/scripts/adr.py index --dir docs/decisions --json
```

## What Happens

1. `init --locale ko` sets `"locale": "ko"` in `.adr-toolkit.json` at the repository root.
2. `create` reads the input draft containing the Korean title `결제 서비스 이벤트 기반 아키텍처 도입`, validates the approved slug `event-driven-payment-architecture`, and creates `docs/decisions/0002-event-driven-payment-architecture.md`.
3. `index` reads `.adr-toolkit.json` locale configuration and renders localized headers (`# 결정 기록`, `## 상태별`, `## 태그별`) in `docs/decisions/README.md`.
4. Field names, IDs (`ADR-0002`), status values (`accepted`), and filenames remain ASCII machine contracts.

## Output

### 1. Repository Configuration (`.adr-toolkit.json`)

```json
{
  "schema_version": 1,
  "locale": "ko"
}
```

### 2. Created Localized ADR Output

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

### 3. Generated Localized Decision Index (`docs/decisions/README.md`)

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
