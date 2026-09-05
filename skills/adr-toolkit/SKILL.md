---
name: adr-toolkit
description: Initialize, record, and check Architecture Decision Records by inspecting the repository and existing decisions before asking questions.
user-invocable: true
version: 1.0.1
---

# ADR Toolkit

## Workflow contract

Operations use the applicable stages from this model. Each operation-specific
section governs omitted or renamed stages; for example, Lifecycle operations
do not run DISCOVER, and RECORD names evidence gathering explicitly.

```text
PREFLIGHT
→ DISCOVER
→ CLASSIFY
→ ASK-IF-NEEDED
→ PLAN
→ CONFIRM
→ MUTATE
→ VALIDATE
→ REPORT
```

## Language

Use one of the canonical locales `en`, `ko`, `ja`, `zh`, `fr`, `es`, `de`,
or `pt-BR`; `zh` means Simplified Chinese. Compose agent-authored questions
and reports using this precedence: explicit user request → request language →
repository default in `.adr-toolkit.json` → `en`. Do not translate prose the
user already supplied.

The deterministic CLI resolves locale as explicit `--locale` → approved input
draft `locale` → repository default → `en`. Normally omit repeated flags when
the repository default matches the request; pass `--locale` only for an
explicit per-operation override. For example:

```bash
python skills/adr-toolkit/scripts/adr.py index --dir docs/decisions --locale fr --json
```

INIT and CREATE localize deterministic prompts and MADR structure. INDEX
localizes its generated headings. IDs, status values, JSON keys, error codes,
and filenames remain English/ASCII machine contracts.

## INIT (scaffolding only)

Use INIT when a repository has no ADR directory yet. INIT does not mine
history — it only sets up the structure. Run DISCOVER afterward (or any
time later) to recover past decisions.

1. **PREFLIGHT** — run `python skills/adr-toolkit/scripts/adr.py preflight --json`. If
   `existing_adr_directory` is set, stop and tell the user an ADR directory
   already exists; do not scaffold a second one.
2. **CONFIRM** — show the user the exact directory that will be created,
   before writing anything.
3. **MUTATE** — run `python skills/adr-toolkit/scripts/adr.py init --locale <code> --dir docs/decisions --json`
   to create `.adr-toolkit.json`, the directory, template, and ADR-0001.
4. **VALIDATE** — run `python skills/adr-toolkit/scripts/adr.py validate --dir docs/decisions --json`
   and `python skills/adr-toolkit/scripts/adr.py index --dir docs/decisions --json`.
5. **REPORT** — tell the user INIT is done and that they can run DISCOVER
   next if they want to recover past decisions from the repository's
   history.

## DISCOVER (past-decision recovery)

Use DISCOVER on a repository that already has an ADR directory (run INIT
first if it doesn't). DISCOVER can be run once right after INIT, skipped
entirely, or re-run later to mine more of the history incrementally.

1. **PREFLIGHT** — run `python skills/adr-toolkit/scripts/adr.py preflight --json`. If
   `existing_adr_directory` is `null`, stop and tell the user to run INIT
   first.
2. **GATHER EVIDENCE** — run `python skills/adr-toolkit/scripts/adr.py discover --json` from
   the repository root. Read the `dependencies` list; each entry is
   candidate evidence for a past architectural decision (e.g. `pom.xml`
   suggests a JVM build-tool decision was made, even if undocumented).
3. **CLASSIFY** — for each finding, decide whether it looks structural (a
   database driver, a message broker, a web framework) versus routine
   tooling (a linter, a test runner), using the table below. Only
   structural choices are candidates.
4. **ASK-IF-NEEDED** — consult `references/interview-guide.md` before asking
   questions and follow its priority order, at-most-3-per-round cap,
   no-known-facts rule, and ambiguity follow-up rule. For each candidate, ask
   the highest-priority unanswered question only if the reason is not evident
   from comments, README, or commit history. Do not ask about anything
   `discover` already reported as a fact.
5. **PLAN** — draft a `retrospective: true` MADR body for each ADR the user
   wants recorded, following `templates/madr-minimal.md` (see
   `references/madr-guide.md` for when to use the full template instead).
   Every retrospective body MUST contain three separate subsections, never
   merged into one narrative:

   ```markdown
   ## Confirmed Evidence

   * {only facts `discover` or the user's own words actually established}

   ## Inferred Rationale

   * {the agent's best guess at *why*, explicitly labeled as a guess}

   ## Unknown

   * {anything about the original decision that cannot be recovered from this repository}
   ```

6. **CONFIRM** — show the user each candidate's title, confirmed evidence,
   and inferred rationale before writing anything; the user can drop any
   candidate.
7. **MUTATE** — for each approved candidate, write a draft JSON file
   (`title`, `status`, `body` — body includes the three-part structure
   above — plus any of `date`/`decision_makers`/`related`/
   `affected_paths`/`tags`/`retrospective`) and run
   `python skills/adr-toolkit/scripts/adr.py create --input <draft.json> --dir docs/decisions --json`.
8. **VALIDATE** — same as INIT step 4. If validate reports errors, fix the
   draft and re-run `create` — never hand-edit the generated file to patch
   a validation error.
9. **REPORT** — tell the user what was created, in this order: facts
   found, judgment, questions asked, files created, validation result,
   remaining uncertainty.

## What belongs in an ADR

Not every structural-looking finding deserves a new file. Apply this table
during CLASSIFY, in INIT/DISCOVER and RECORD:

| Content | Where it belongs |
|---|---|
| Structural, long-lived decision | ADR |
| Feature implementation detail | Pull request |
| Routine code-change rationale | Commit message |
| Usage/behavior explanation | README or docs |
| Incident/outage response | Incident report / postmortem |
| A rule that must hold going forward | ADR's Implementation Constraints |

## RECORD

Use RECORD for both a forward-looking decision question and a retrospective
request to find decisions in a branch or diff. The trigger changes; the
workflow does not.

1. **PREFLIGHT** — run
   `python skills/adr-toolkit/scripts/adr.py preflight --json`. If
   `existing_adr_directory` is `null`, stop and tell the user to run INIT
   first.
2. **GATHER EVIDENCE** — inspect the affected repository paths; for a
   retrospective request, inspect the requested branch/diff range. Before
   drafting, run `related` with only evidence-backed optional filters, for
   example:
   `python skills/adr-toolkit/scripts/adr.py related --paths src/events deploy/kafka --tags kafka messaging --keyword broker --dir docs/decisions --json`.
   Values after `--paths` and `--tags` are space-separated, not comma-joined.
   Omit `--paths`, `--tags`, or `--keyword` when that evidence is unknown;
   never invent a path, tag, or keyword. Use the results to find ADRs that
   already cover, conflict with, or may be replaced by the candidate.
   `related`'s filters are OR'd together (any single overlap is enough) — it
   deliberately casts a broad net before drafting. For a general lookup
   unrelated to drafting (a user asks "has this been decided before?" or
   "what ADRs govern `src/payment/`?"), use `search` instead — its filters
   combine with AND for precise results, it supports `--status` and
   `--path` (real-file-vs-governed-scope, not an exact list match), it
   ranks results best-match-first, and an empty query browses every ADR.
   See README's "Search" section for the full contract.
3. **CLASSIFY** — apply the table above, then read
   `references/significance-rules.md`. Score only evidence-supported 0/1/2
   values; never guess or inflate a score to force a band. Write all seven
   scores to `scores.json` and run
   `python skills/adr-toolkit/scripts/adr.py significance --input scores.json --json`.
   For `not_needed`, recommend a commit message or code comment instead; for
   `optional`, let the user decide; for `recommended`, continue. The user may
   override any band and ask to record the ADR.
4. **ASK-IF-NEEDED** — follow `references/interview-guide.md`, ask no more
   than 3 substantive questions per round, and skip facts already established
   by the request, repository, diff, discovery, or related ADRs. Each
   independently answerable priority item counts as one question; never bundle
   items to bypass the cap, and defer lower-priority items after three.
5. **PLAN** — draft per `references/madr-guide.md`: use the full MADR for at
   least three realistic alternatives and for the guide's other full-template
   triggers; otherwise use the minimal MADR. Every retrospective RECORD MUST
   preserve the separate Confirmed Evidence, Inferred Rationale, and Unknown
   subsections defined in DISCOVER. Use `related` results to identify a
   possible replacement, but do not assume supersession.
   If the decision is mechanically checkable (a forbidden import, a required
   companion file, a boundary that must not be crossed), add an
   `Implementation Constraints` section with a `constraints:` block so CHECK
   can enforce it — see `references/conflict-rules.md` for the six rule kinds
   and the exact block syntax.
6. **CONFIRM** — before any `create`, show the title, problem, considered
   options, decision, primary driver, accepted downside, affected paths, and
   the proposed semantic ASCII slug. For a non-ASCII title, suggest a useful
   slug but never translate or transliterate inside the deterministic core.
   Get explicit approval of the draft. If it may replace an Accepted ADR,
   separately confirm that supersession is intended.
7. **MUTATE** — write the approved draft JSON and run
   `python skills/adr-toolkit/scripts/adr.py create --input <draft.json> --slug <approved-slug> --dir docs/decisions --json`.
   Only after explicit supersession intent and approval, follow the
   supersede preview and mutation sequence in Lifecycle operations; never
   hand-edit lifecycle fields or links.
8. **VALIDATE** — run
   `python skills/adr-toolkit/scripts/adr.py validate --dir docs/decisions --json`
   and
   `python skills/adr-toolkit/scripts/adr.py index --dir docs/decisions --json`.
9. **REPORT** — report facts found, judgment and significance result,
   questions asked, files created or updated, validation result, and remaining
   uncertainty.

## Lifecycle operations

Lifecycle changes are explicit and user-triggered. First run
`python skills/adr-toolkit/scripts/adr.py preflight --json`. If
`existing_adr_directory` is `null`, stop and direct the user to INIT; do not
run a lifecycle dry-run against an absent directory. Otherwise, preview with
`--dry-run --json`, show the old status -> new status or the supersession link
pair, and ask for confirmation. Only then run the same command without
`--dry-run`. Never hand-edit `status`, `superseded_by`, or `supersedes`.

| User intent | Preview | After confirmation |
|---|---|---|
| Accept an ADR | `python skills/adr-toolkit/scripts/adr.py status <N> --to accepted --dir docs/decisions --dry-run --json` | `python skills/adr-toolkit/scripts/adr.py status <N> --to accepted --dir docs/decisions --json` |
| Deprecate an ADR without a replacement | `python skills/adr-toolkit/scripts/adr.py deprecate <N> --dir docs/decisions --dry-run --json` | `python skills/adr-toolkit/scripts/adr.py deprecate <N> --dir docs/decisions --json` |
| Supersede an ADR with another | `python skills/adr-toolkit/scripts/adr.py supersede <old-number> --by <new-number> --dir docs/decisions --dry-run --json` | `python skills/adr-toolkit/scripts/adr.py supersede <old-number> --by <new-number> --dir docs/decisions --json` |

After a successful mutation, run the same validate and index commands as
RECORD, using the repository locale unless the user requested an explicit
override. If a preview or mutation returns `INVALID_TRANSITION`, stop and
explain the rejected transition using `references/lifecycle.md`; do not retry
with a different status or bypass the script.

## CHECK

Use CHECK to look for structural conflicts between a diff and existing
Accepted/Superseded ADRs before or during a change — never after merging,
since CHECK is read-only and never fixes anything itself.

1. **PREFLIGHT** — run
   `python skills/adr-toolkit/scripts/adr.py preflight --json`. If
   `existing_adr_directory` is `null`, stop and tell the user to run INIT
   first.
2. **GATHER EVIDENCE** — run
   `python skills/adr-toolkit/scripts/adr.py check --uncommitted --dir docs/decisions --json`
   (or `--staged`, or `--since <ref>` for a branch/commit range — pick the
   mode that matches what the user asked to check). Read
   `references/conflict-rules.md` if you need to explain a finding or help
   the user write a `constraints:` block.
3. **CLASSIFY** — each finding already carries both its `kind` (`related`,
   `review_required`, `verified_violation`, `no_applicable_constraint`) and a
   `confidence` field (`VERIFIED`, `VIOLATED`, or `UNVERIFIABLE`) computed by
   the deterministic core — do not re-judge or recompute it, report it as
   returned. See `references/conflict-rules.md` for what each value means. No
   related finding at all is `NOT_APPLICABLE`, not proof that the repository
   is compliant.
4. **REPORT** — group findings by classification. For every Verified violation
   finding, present all five resolutions from
   `references/conflict-rules.md` (`fix_code`, `supersede_adr`,
   `adjust_scope`, `register_exception`, `false_positive`) — never assume
   which one the user wants.
5. **ASK-IF-NEEDED / MUTATE** — CHECK itself never writes anything. If the
   user picks `fix_code`, that's a normal code edit, not an ADR Toolkit
   operation. If they pick `supersede_adr` or `adjust_scope`, follow the
   RECORD or Lifecycle operations flow above — never hand-edit
   `constraints:`, `affected_paths`, or `status`. If they pick
   `register_exception`, gather `adr_id`, `rule_id`, `owner`, `reason`, a
   narrow `scope` (never the whole rule), and an `expiry`, then run
   `python skills/adr-toolkit/scripts/adr.py exception --input <file.json> --dir docs/decisions --json`
   — never hand-write a file under `docs/decisions/exceptions/`. A finding
   already carrying an `exception` field has a matching, non-expired record;
   report it, don't re-register it.
6. Any `check` `warnings` entries (e.g. `BAD_FRONTMATTER`, `SCHEMA_ERROR`,
   `BAD_CONSTRAINTS`, `BAD_EXCEPTION`) mean one ADR, constraint, or exception
   was skipped, not that CHECK failed — report them and never describe a
   warning-bearing result as clean.

## Prohibited

- Creating `docs/decisions/` when `preflight` already found one.
- Running DISCOVER when `preflight` reports no ADR directory — tell the
  user to run INIT first instead.
- Writing any ADR file before the user has seen and approved its title,
  problem, and decision.
- Marking a retrospective ADR `status: accepted` without the user
  confirming the reconstruction is accurate.
- Guessing a dependency's purpose instead of asking, when it's not evident
  from the repository.
- Merging Confirmed Evidence, Inferred Rationale, and Unknown into a single
  undifferentiated narrative for a retrospective ADR.

## Script reference

All mutating and validating operations are deterministic scripts under
`skills/adr-toolkit/scripts/`; this skill never re-implements ID assignment,
file writes, or schema validation in prose — it only decides what to ask and
what to draft.

CHECK's conflict detection is deliberately limited to structural evidence
from `constraints:` blocks (see `references/conflict-rules.md`). It does not certify the entire architecture
and never attempts semantic or AST-level
analysis; see `project-roadmap.md` for what that fuller scope would look like.

`graph` is a read-only navigation export:

```bash
python skills/adr-toolkit/scripts/adr.py graph --dir docs/decisions --format both --json
```

It writes Mermaid (`relationships.mmd`) and SVG (`relationships.svg`) graph
artifacts from the same relationship model used by `index`. SVG is generated
directly by Python so the image stays sharp without requiring Mermaid CLI,
Node, or browser rendering.
When `--format both` and `--output` are used together, `--output` is a file
prefix; for example `--output build/adr-relationships` writes
`build/adr-relationships.mmd` and `build/adr-relationships.svg`.
