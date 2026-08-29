# ADR Lifecycle Reference

## Statuses

- `proposed` — drafted, not yet approved by a human.
- `accepted` — approved and currently in force.
- `rejected` — considered and explicitly declined.
- `deprecated` — no longer recommended, no direct replacement.
- `superseded` — replaced by a specific later ADR (`superseded_by` must be set).

## Allowed transitions

```text
proposed   -> accepted | rejected
accepted   -> deprecated | superseded
rejected   -> (terminal)
deprecated -> (terminal)
superseded -> (terminal)
```

`scripts/core/lifecycle.py` enforces this table. If a user asks for a
transition that isn't in it, confirm they understand it's non-standard
before doing anything, and never write a status that violates the table.
