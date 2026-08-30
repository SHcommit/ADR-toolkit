# ADR Toolkit localization and pre-0.1.1 readiness design

## Status

Approved in conversation on 2026-08-30. This design defines the work that
must be planned before implementation. It does not itself authorize a
`v0.1.1` release.

## Problem statement

The MVP proves that ADR Toolkit can initialize, discover, record, validate,
index, and check Architecture Decision Records. The next release must prove
something stricter: the toolkit must produce useful ADRs in real repositories,
serve users in their chosen language, and have a credible path from a
single-maintainer GitHub repository to team and enterprise governance.

The current repository exposes four gaps that should be addressed before
`v0.1.1`:

1. Runtime localization covers only five locales and only the generated
   decision-log index. INIT, interactive CREATE, and MADR section headings
   remain English.
2. Non-ASCII-only titles cannot be created because filename slug generation
   accepts only `[a-z0-9]` and returns an empty slug for titles such as
   `결제 시스템 분리`.
3. The dogfooded ADRs pass structural validation but do not yet demonstrate
   the full RECORD quality contract: decision ownership is empty, some
   retrospective decisions are marked as prospective, and affected paths and
   confirmations are narrower than the decisions they describe.
4. `handoff.md`, `improvements.md`, and `project-roadmap.md` contain stale or
   overlapping state. Work selected for implementation needs to move into
   `improvements.md`; it should no longer remain an unscheduled roadmap item.

## Goals

- Generate ADRs in English, Korean, Japanese, Simplified Chinese, French,
  Spanish, German, and Brazilian Portuguese.
- Let the user choose a locale explicitly and let an agent infer it from the
  user's request when no explicit choice exists.
- Preserve user-authored text instead of applying opaque machine translation.
- Keep filenames portable across Git, macOS, Linux, Windows, URLs, and common
  agent harnesses.
- Correct and strengthen this repository's unreleased dogfooded ADR set.
- Publish a Korean, evidence-backed readiness and enterprise-adoption report.
- Give `handoff.md`, `improvements.md`, `project-roadmap.md`, and the new report
  non-overlapping responsibilities.
- Define public-repository governance as a planned transition, not misclassify
  its present absence as a defect in a deliberately private repository.

## Non-goals

- Maintaining eight translated copies of every ADR.
- Translating arbitrary user prose after it has been written.
- Translating the full project README and contributor documentation into eight
  separate documents in this change.
- Building a GitHub App, central decision portal, vector database, or multi-repo
  graph before the local workflow and GitHub Action integration are proven.
- Enabling GitHub branch protection while the private repository's current plan
  does not expose that feature.

## Objective baseline assessment

Scores use a five-point scale: 1 means a prototype with material adoption
barriers, 3 means usable by a small team with known manual controls, and 5
means repeatable enterprise operation with measured controls. These are
readiness scores, not code-quality grades.

| Dimension | Current | Evidence | Pre-0.1.1 target |
|---|---:|---|---:|
| Deterministic core | 4.0 | 212 tests pass; ID, lifecycle, validation, index, diff, and release paths are scripted | 4.3 |
| ADR content quality | 2.5 | Five ADRs validate, but all omit decision makers and the retrospective contract is not consistently represented | 4.0 |
| Internationalization | 2.0 | Five index locales exist; prompts, templates, and non-ASCII title creation are incomplete | 4.0 |
| CHECK correctness | 3.0 | Structural rules work; rename handling, ignored-path discovery, and a second subprocess failure remain open | 3.8 |
| Developer experience | 3.5 | Root README and executable quickstart exist; CLI output semantics and locale behavior remain inconsistent | 4.2 |
| Distribution parity | 2.8 | Four harness paths are documented, but only some were exercised end to end | 3.3 |
| Repository governance | 2.5 | Git Flow and CI exist; the private repository intentionally has no enforceable branch rules, CODEOWNERS, or review template | 3.0 before public, 4.0 after public |
| Enterprise scalability | 1.8 | No organization ruleset, cross-repo catalog, RBAC model, exception workflow, audit export, or adoption metrics | 2.2 |

The target is deliberately incremental. `v0.1.1` should make the local product
and its own ADRs trustworthy; it should not pretend to complete enterprise
governance in one release.

## Chosen approach

Extend the existing deterministic scripts and locale catalog. Do not add a
separate translation program and do not create translated ADR replicas.

The alternatives were:

1. Add three index locale files only. This is cheap but leaves the actual ADR
   creation workflow English-only and does not solve non-ASCII titles.
2. Localize the complete generation boundary while preserving user prose.
   This is the selected approach because it covers both agent-mediated and
   standalone CLI usage without introducing translation drift.
3. Generate and synchronize eight complete translations of every ADR. This is
   rejected because approval, supersession, links, and content corrections
   would diverge across replicas.

## Locale model

### Supported locales

The canonical locale set is:

```text
en, ko, ja, zh, fr, es, de, pt-BR
```

`zh` means Simplified Chinese. A future Traditional Chinese locale must use a
distinct code such as `zh-TW` rather than changing the meaning of `zh`.

### Selection precedence

For agent-mediated workflows:

```text
explicit language requested by the user
→ language detected from the user's request
→ en
```

For standalone CLI workflows:

```text
explicit --locale
→ en
```

The standalone CLI does not guess from the operating-system locale. That would
make automation depend on the machine running it and would make CI output less
reproducible.

An unsupported locale is a user error. It must not silently become English.
A shipped locale file that is missing or malformed may degrade to the complete
English base at runtime, but the test suite and release checks must reject that
state before publishing.

### What is localized

- INIT's generated ADR body and repository ADR template.
- Interactive CREATE prompts and generated Minimal MADR headings.
- Minimal and Full MADR section labels used by agent guidance.
- Decision-log headings and status display labels.
- Human-readable README examples and locale documentation.

Machine contracts remain stable:

- CLI command names and flags stay English.
- JSON field names, operation names, error codes, status values, and rule kinds
  stay locale-neutral English identifiers.
- File encoding remains UTF-8.

### ADR metadata

Newly generated ADRs carry an optional `locale` frontmatter field:

```yaml
locale: ko
```

It is optional for backward compatibility with ADRs created by earlier
versions or by other tools. ADR Toolkit-generated files always include it.
Validation rejects an unsupported value when the field exists. The external
JSON Schema and runtime validator must remain in parity.

The locale records the language selected for generated structure. It does not
claim that every code identifier, quotation, or linked document in the body is
written in that language.

## Portable filename policy

ADR titles and bodies support Unicode. Filenames remain ASCII because Unicode
normalization and tool behavior can differ across platforms and integrations.

Creation follows this order:

1. Use an explicitly supplied ASCII `slug` when present and valid.
2. Otherwise derive the existing ASCII slug from the title when non-empty.
3. Otherwise use the locale-neutral fallback `decision`.

Examples:

```text
title: Use Kafka for events       → 0006-use-kafka-for-events.md
title: 결제 시스템 분리           → 0006-decision.md
title: 결제 시스템 분리, slug: separate-payment-system
                                  → 0006-separate-payment-system.md
```

The numeric ADR ID guarantees uniqueness, so a repeated fallback slug is not a
collision. The parser continues to accept the established ASCII filename
contract.

## Component changes

### Locale catalog

`scripts/i18n/*.json` becomes the single catalog for deterministic text. The
English file defines the complete key set; each other locale must match it
exactly. Keys cover index labels, statuses, MADR headings, INIT boilerplate,
and interactive prompts.

### Locale loader

`scripts/core/locale.py` owns the canonical locale list, catalog loading,
fallback behavior, and completeness checks. CLI parsers import the same list
instead of duplicating choices.

### Template rendering

A focused template-rendering module converts locale strings and user-provided
answers into Minimal or Full MADR Markdown. Interactive CREATE and INIT call
this renderer rather than maintaining English prose inline. Agent-authored
draft bodies remain accepted as opaque approved Markdown.

### Command behavior

- `init --locale <code>` localizes generated files and records locale metadata.
- `create --interactive --locale <code>` localizes prompts and structure.
- `create --input` accepts optional `locale` and `slug` draft fields.
- `index --locale <code>` keeps its existing responsibility and gains the
  three new locales.
- `validate` checks a present locale and all existing relationship invariants.

## Dogfooding corrections

The five current ADR files were added after the `v0.1.0` tag and have not yet
shipped from `master`. They may therefore be corrected before their first
release without rewriting a released decision log.

The correction set is:

- Record `YangSeungHyun` as the decision maker because the repository owner
  explicitly approved the decisions before commit.
- Add `locale: en` to the existing English ADRs.
- Keep every status `accepted`.
- Mark ADR-0002 through ADR-0004 retrospective and separate confirmed
  evidence, inferred rationale, and unknowns as required by the toolkit.
- Treat ADR-0005 as contemporaneous unless contrary evidence is supplied.
- Expand ADR-0004 to Full MADR because it compares three realistic options.
- Correct affected paths, relationships, confirmation evidence, and the INIT
  ADR's visibly incomplete confirmation checkbox.
- Evaluate missing core decisions—Deterministic Core / Agentic Edge, no silent
  mutation, and lifecycle/link invariants—using the significance rubric before
  deciding whether to add ADRs.
- Add CHECK constraints only where the rule vocabulary can prove the policy
  without misleading false confidence.

After release, Accepted ADR content becomes append-only: a changed decision is
recorded as a new ADR and linked through supersession. Narrow factual metadata
corrections need an explicit documented policy rather than silent edits.

## Readiness and enterprise-adoption report

Create:

```text
docs/adr-toolkit-readiness-and-enterprise-adoption-report.md
```

The report is Korean and distinguishes four evidence classes:

1. Repository fact, linked to a file, test, command result, commit, PR, or
   workflow run.
2. External practice, linked to an official primary source.
3. Inference, explicitly labeled and tied to its evidence.
4. Recommendation, including priority, cost, dependency, and acceptance
   signal.

Its sections are:

- Executive assessment and maturity table.
- Product architecture and dependency boundaries.
- ADR dogfooding quality audit.
- `improvements.md`, `handoff.md`, and roadmap reconciliation.
- Reliability, security, portability, and developer-experience gaps.
- Public GitHub transition checklist.
- Team and enterprise adoption model.
- Prioritized release gates and longer-term investments.
- Risks, invalidation triggers, and measurable success criteria.

## Work-tracking document boundaries

### `handoff.md`

Contains only the active task, touched files, next step, and open risk. Remove
the stale statement that the MVP feature branch is not integrated.

### `improvements.md`

Contains concrete implementation work selected for execution. Add the
localization, dogfooding corrections, report, CHECK correctness work, and
public-transition preparation that have actionable acceptance criteria.

### `project-roadmap.md`

Contains unscheduled product bets. Remove items promoted to
`improvements.md`, including localized MADR headings. Keep genuine later bets
such as semantic conflict analysis, relationship visualization, multi-repo
graphs, central portals, and external-system integrations.

### Readiness report

Captures the assessment snapshot and why the priorities were chosen. It does
not become a second task tracker.

## GitHub governance transition

### Current private phase

The repository is private. Its current plan returns HTTP 403 for branch
protection and repository ruleset APIs. This is a platform-plan constraint and
an intentional pre-public state, not evidence that the documented Git Flow
policy was forgotten.

CI has run successfully on the first pull request and on `develop`, `master`,
and the release tag. The limitation is enforcement: GitHub cannot currently
prevent a direct push or an unreviewed merge.

### Public transition gate

When the owner makes the repository public, apply and verify:

- Branch protection or repository rulesets for `master` and `develop`.
- Pull requests required before merge.
- Required ADR validation, test, and version-drift checks.
- Required conversation resolution.
- Force-push and deletion blocking.
- `CODEOWNERS` coverage for `docs/decisions/`, schemas, lifecycle code, and
  release workflows.
- A pull-request template with an ADR impact declaration.
- Tag protection or a tag ruleset for `v*` releases.
- A documented bypass policy for emergencies.
- A deliberate decision on signed commits rather than enabling them without a
  bot and contributor migration plan.

GitHub settings must be verified through the API after configuration. A policy
written only in `AGENTS.md` is not an enforcement signal.

### Team adoption

Before presenting the toolkit as team-ready, add:

- Explicit ADR owner and stakeholder semantics.
- Proposed → review → accepted workflow guidance.
- CODEOWNER review for decision-log changes.
- An ADR-impact field in pull requests: not applicable, covered by an existing
  ADR, proposes a new ADR, or conflicts with an ADR.
- A CI job that runs validate, detects stale generated indexes, and runs CHECK
  against the pull-request base.
- An exception record with owner, reason, scope, and expiry when a verified
  violation is intentionally tolerated.
- Review cadence and stale-decision reporting without automatically mutating
  Accepted ADRs.

### Enterprise adoption

Enterprise capabilities remain phased roadmap work until team usage produces
evidence that they are needed:

- Organization-level rulesets and reusable workflows.
- Central discovery across repositories without destroying repository-local
  ownership.
- RBAC mapping for proposer, owner, reviewer, approver, and exception authority.
- Audit-log export and decision/review correlation.
- Controlled taxonomy for tags, domains, risk, and compliance mappings.
- Policy-as-code checks and architecture fitness functions.
- SSO-aware GitHub App or service integration only after a GitHub Action proves
  the review workflow.
- Adoption metrics: time to decision, review latency, supersession rate,
  unresolved violations, exception age, and stale-decision review coverage.

The design deliberately rejects building a central portal first. A portal
would centralize weak or inconsistent records rather than fix their quality.

## External evidence baseline

- AWS Prescriptive Guidance defines ADR ownership, Proposed-state review,
  stakeholder recording on acceptance, immutable accepted records, and
  supersession instead of overwriting:
  <https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html>
- AWS recommends distributed ownership, preserved history, regular review,
  central accessibility, and explicit handling of non-compliant legacy code:
  <https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/best-practices.html>
- Microsoft recommends an append-only decision log, retrospective recovery for
  brownfield systems, confidence recording, consistent anatomy, and standalone
  rationale:
  <https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record>
- GitHub documents required pull requests, CODEOWNER approval, required status
  checks, code scanning, force-push controls, and tag/branch rulesets:
  <https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets>
- GitHub organization rulesets can apply governance across repositories and
  expose evaluation insights:
  <https://docs.github.com/en/organizations/managing-organization-settings/managing-rulesets-for-repositories-in-your-organization>

## Verification plan

### Localization

- Every locale has exactly the English catalog's required keys.
- CLI accepts all eight locale codes, rejects unknown codes, and defaults to
  English when omitted.
- Each locale passes INIT → interactive CREATE → VALIDATE → INDEX in a scratch
  repository.
- Each generated body contains the expected localized headings.
- Non-ASCII-only, mixed-script, and explicit-slug titles create stable files.
- ADRs without locale remain valid; unsupported present locales fail.
- JSON Schema and runtime validation remain in parity.

### Dogfooding and documentation

- All repository ADRs validate.
- The decision index regenerates without a diff.
- Confirmation claims are checked against actual files and commands.
- CHECK runs against a representative conforming and violating change.
- README commands execute as written.
- `handoff.md`, `improvements.md`, and `project-roadmap.md` contain no duplicate
  active items and no claims contradicted by the Git graph.

### Repository

- Full pytest suite passes freshly.
- Version sync check passes.
- Workflow YAML remains valid.
- Working tree contains only intended changes.
- Public GitHub protections are not claimed complete until API verification
  succeeds after the repository is made public.

## Delivery order

1. Update work-tracking documents and write the readiness report.
2. Implement locale catalog and rendering boundaries with tests.
3. Implement portable slug fallback and locale metadata with compatibility
   tests.
4. Update README, examples, and agent guidance.
5. Correct the unreleased dogfooded ADRs and regenerate their index.
6. Fix pre-release CHECK correctness items selected in `improvements.md`.
7. Run complete verification and perform a final pre-`0.1.1` review.
8. After the repository becomes public, configure and API-verify GitHub
   protections as a separate operational task.

## Decision and revisit triggers

Adopt complete generation-boundary localization with one approved ADR per
decision, not translated replicas. Keep deterministic machine contracts in
English and portable filenames in ASCII.

Revisit this design if:

- Users require bilingual ADRs rather than one chosen language.
- A supported harness cannot read UTF-8 bodies reliably.
- Generic fallback filenames materially harm navigation at scale.
- Translation maintenance produces repeated correctness defects.
- Team adoption demonstrates that locale belongs at repository level rather
  than per ADR.
- Public or enterprise GitHub settings materially change the available
  enforcement model.
