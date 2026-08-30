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

### Pattern syntax is kind-specific

Every value in `paths` uses the toolkit's **glob** syntax. For
`forbidden_import` and `dependency_forbidden`, each `pattern` value is a
Python **regular expression** matched against added lines. For `required_path`
and `forbidden_path`, each `pattern` value is another glob matched against
repository paths. `file_must_exist` and `test_must_exist` use their `paths`
globs directly and do not require `pattern`.

For example, the glob `src/**/*.py` matches Python files at any depth below
`src/`. Writing `src/**\\.py` as though it were a regular expression is
incorrect: glob `**` traversal and regex escaping are different languages.
Conversely, a `forbidden_import` content pattern such as `openai\\.` is a
regular expression, not a path glob.

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

## Evidence confidence

Every finding carries this mapping directly as a `confidence` field — reading
it off `kind` yourself is only needed to explain *why* a confidence value
applies, not to compute it:

| Existing `kind` | `confidence` field | Meaning |
|---|---|---|
| `related` | **VERIFIED** | Only for the applicable explicit structural rules in this diff. |
| `verified_violation` | **VIOLATED** | By direct structural evidence. |
| `review_required` | **UNVERIFIABLE** | Without human review. |
| `no_applicable_constraint` | **UNVERIFIABLE** | For the related ADR, because no usable rule proved the policy. |
| No related ADR or finding | **NOT_APPLICABLE** | To the known scoped rules — an empty `findings` list, not a global pass. |

CHECK does not certify the entire architecture. A successful command means
the requested evidence was collected and evaluated; it does not prove prose,
organizational rationale, runtime behavior, or every architectural invariant.

## Resolving a Verified violation

Present all five options; never default to "revert the code":

1. `fix_code` — change the diff to comply with the existing decision.
2. `supersede_adr` — the old decision no longer holds; record a new ADR
   that supersedes it (`adr.py supersede`).
3. `adjust_scope` — the ADR's `affected_paths` or `constraints:` are too
   broad or too narrow. If the ADR is still Proposed, revise it through the
   RECORD approval flow. If it is Accepted, record and approve a replacement
   ADR, then supersede the old one; never weaken an accepted record in place
   merely to clear CHECK.
4. `register_exception` — this specific case is a deliberate, documented
   exception to an otherwise-still-valid rule. Record it deterministically:

   ```bash
   python skills/adr-toolkit/scripts/adr.py exception --input exception.json \
     --dir docs/decisions --json
   ```

   `exception.json` must provide `adr_id`, `rule_id`, `owner`, `reason`,
   `scope` (path patterns the exception is narrowed to — never the whole
   rule), and `expiry` (`YYYY-MM-DD`); the command assigns the next `EXC-NNNN`
   id and writes `docs/decisions/exceptions/NNNN.json`. A future CHECK run on
   a matching, non-expired exception annotates the finding with an
   `exception` field — the finding's `kind` and `confidence` stay
   `verified_violation`/`VIOLATED`; an exception is visible evidence, never a
   silent pass. An expired exception stops applying automatically; register a
   new one to extend it, never edit the `expiry` of an existing record.
5. `false_positive` — the rule fired but there is no real conflict; note
   why so the rule can be tightened.
