# Conflict Rules Reference

CHECK matches a diff against Accepted ADRs' `constraints:` blocks and
Superseded ADRs' `affected_paths` — structural evidence only, never
semantic/AST analysis (see the design spec §7).

## Writing a `constraints:` block

Add a fenced YAML block to an ADR's `Implementation Constraints` section:

```yaml
constraints:
  - id: no-provider-sdk-in-feature
    kind: forbidden_import
    paths: ["src/features/**"]
    pattern: ["openai\\.", "anthropic\\."]
    severity: major
    message: "Feature modules must use the LLM port."
```

Each rule needs `id`, `kind`, `paths` (glob list, `**` matches any depth),
`severity`, and `message`; `pattern` is required by every kind except the
existence-check kinds. `paths`/`pattern` values must be a JSON-style array
on one line — not YAML block-list syntax.

## The six rule kinds

- `forbidden_import` — fires if an added line in a file matching `paths`
  matches any regex in `pattern`. Use for "this module must never import X."
- `dependency_forbidden` — mechanically identical to `forbidden_import`;
  scope `paths` to a dependency manifest (`requirements.txt`,
  `package.json`) instead of source files.
- `required_path` — fires if the diff touches a file matching `paths` but
  no file matching `pattern` is touched by the diff or already exists in
  the repository. Use for "touching X requires also touching/having Y."
- `forbidden_path` — fires if the diff touches a file matching `paths` AND
  also touches a file matching `pattern`. Use for boundary violations
  ("features must never touch db migrations directly").
- `file_must_exist` / `test_must_exist` — fires if none of the paths
  matching `paths` exist in the working tree after the diff. Identical
  mechanism; `test_must_exist` is a naming convention for the ADR author,
  not different logic.

An ADR with no `constraints:` block has nothing CHECK can mechanically
enforce — that's a legitimate state, not an error.

## Four-way classification

- **Related** — the diff touches a path the ADR names, and its
  `constraints:` block was evaluated but nothing fired.
- **Review required** — the ADR's `Confirmation` (or `Verification`)
  section references a path or test that the diff removes, or that was
  never created at all; this is prose-scanning, not a `constraints:` rule,
  so it needs a human look rather than a mechanical yes/no.
- **Verified violation** — a `constraints:` rule fired with direct
  structural evidence, or the diff touches a path a Superseded ADR
  governs (`rule_id: superseded_reference`).
- **No applicable constraint** — the diff touches a path the ADR names,
  but the ADR has neither a usable `constraints:` block nor a matching
  Confirmation/Verification reference. An unparseable block (unknown field,
  unknown `kind`, or an invalid regex in `pattern`) also lands here, with a
  `BAD_CONSTRAINTS` warning — it is never silently reported as Related.

## Resolving a Verified violation

Present all five options; never default to "revert the code":

1. `fix_code` — change the diff to comply with the existing decision.
2. `supersede_adr` — the old decision no longer holds; record a new ADR
   that supersedes it (`adr.py supersede`).
3. `adjust_scope` — the ADR's `affected_paths` or `constraints:` are too
   broad or too narrow; edit them instead of the code.
4. `register_exception` — this specific case is a deliberate, documented
   exception to an otherwise-still-valid rule.
5. `false_positive` — the rule fired but there is no real conflict; note
   why so the rule can be tightened.
