---
name: adr-toolkit
description: Initialize, record, and check Architecture Decision Records by inspecting the repository and existing decisions before asking questions.
user-invocable: true
version: 0.1.0
---

# ADR Toolkit

## Workflow contract

Every operation follows the same nine stages:

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

## INIT (scaffolding only)

Use INIT when a repository has no ADR directory yet. INIT does not mine
history — it only sets up the structure. Run DISCOVER afterward (or any
time later) to recover past decisions.

1. **PREFLIGHT** — run `python skills/adr-toolkit/scripts/adr.py preflight --json`. If
   `existing_adr_directory` is set, stop and tell the user an ADR directory
   already exists; do not scaffold a second one.
2. **CONFIRM** — show the user the exact directory that will be created,
   before writing anything.
3. **MUTATE** — run `python skills/adr-toolkit/scripts/adr.py init --dir docs/decisions` to
   scaffold the directory, template, and ADR-0001.
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
   `python skills/adr-toolkit/scripts/adr.py create --input <draft.json> --dir docs/decisions`.
8. **VALIDATE** — same as INIT step 4. If validate reports errors, fix the
   draft and re-run `create` — never hand-edit the generated file to patch
   a validation error.
9. **REPORT** — tell the user what was created, in this order: facts
   found, judgment, questions asked, files created, validation result,
   remaining uncertainty.

## What belongs in an ADR

Not every structural-looking finding deserves a new file. Apply this table
during CLASSIFY, in both INIT/DISCOVER and (once built) RECORD:

| Content | Where it belongs |
|---|---|
| Structural, long-lived decision | ADR |
| Feature implementation detail | Pull request |
| Routine code-change rationale | Commit message |
| Usage/behavior explanation | README or docs |
| Incident/outage response | Incident report / postmortem |
| A rule that must hold going forward | ADR's Implementation Constraints |

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
`scripts/`; this skill never re-implements ID assignment, file writes, or
schema validation in prose — it only decides what to ask and what to draft.

RECORD and CHECK workflows are not yet implemented (see `project-roadmap.md`
in the repository root and the design spec this skill is built from).
