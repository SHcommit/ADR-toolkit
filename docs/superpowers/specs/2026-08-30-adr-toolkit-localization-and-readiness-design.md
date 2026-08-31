# ADR Toolkit v0.2.0 localization and readiness design

## Status

The initial direction was approved in conversation on 2026-08-30. This revision
incorporates review feedback and awaits final user approval before planning.
The design does not itself authorize a `v0.2.0` release.

## Problem statement

The MVP proves that ADR Toolkit can initialize, discover, record, validate,
index, and check Architecture Decision Records. The next release must prove
something stricter: the toolkit must produce useful ADRs in real repositories,
serve users in their chosen language, and have a credible path from a
single-maintainer GitHub repository to team and enterprise governance.

The current repository exposes four gaps that should be addressed before
`v0.2.0`:

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

## Design principles

### Deterministic Core, Agentic Edge

ADR Toolkit allows an agent to help with judgment, but never makes repository
governance depend on an agent's unvalidated output.

The deterministic core owns:

- IDs and portable filenames.
- Lifecycle transitions and relationship invariants.
- Runtime and JSON Schema validation.
- Locale configuration and catalogs.
- Index generation and CHECK rule evaluation.
- Every mutation of repository ADR state.

The agentic edge may assist with:

- Inferring the user's requested language.
- Drafting ADR prose and extracting rationale from evidence.
- Suggesting a semantic ASCII filename slug.
- Finding related decisions and assessing significance.
- Explaining findings and presenting alternatives to a human.

Agent output crosses a deterministic validation boundary before it becomes
repository state.

### Human-localized, machine-stable

Humans and agents author prose directly in the chosen language. Machine
contracts—IDs, statuses, JSON keys, error codes, rule kinds, and filenames—stay
stable across locales. ADR Toolkit does not maintain opaque automatic
translations as parallel sources of truth.

### Repository-local ownership

The repository remains the source of truth for its decisions, configuration,
owners, and history. Future central discovery may index repository-local ADRs;
it must not replace or silently mutate them.

### No false governance confidence

CHECK reports only what explicit evidence can prove. A passing structural rule
does not mean that an entire architecture is compliant. Policies that cannot be
evaluated deterministically remain visibly unverifiable and require human
review.

## Goals

- Generate ADRs in English, Korean, Japanese, Simplified Chinese, French,
  Spanish, German, and Brazilian Portuguese.
- Let the user choose a locale explicitly and let an agent infer it from the
  user's request when no explicit choice exists.
- Preserve user-authored text instead of applying opaque machine translation.
- Keep filenames portable across Git, macOS, Linux, Windows, URLs, and common
  agent harnesses.
- Correct and strengthen this repository's unreleased dogfooded ADR set.
- Publish separate Korean readiness and enterprise-adoption reports.
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

Maturity uses reproducible integer levels rather than reviewer-selected
decimal scores:

| Level | Meaning |
|---:|---|
| 1 | Prototype or manual experiment; core outcome is not repeatable. |
| 2 | Feature exists, but an important correctness, portability, or workflow gap remains. |
| 3 | Repeatable for an individual or small team with documented manual controls. |
| 4 | Repeatably verified by CI and enforceable repository governance. |
| 5 | Organization-wide policy, audit, exception handling, and measured outcomes exist. |

Each dimension advances only when all of its listed signals are present. The
readiness report records the command, test, workflow, or repository setting
that proves each signal.

| Dimension | Current | Evidence | v0.2.0 target signals |
|---|---:|---|---|
| Deterministic core | 3 | 212 tests pass; ID, lifecycle, validation, index, diff, and release paths are scripted | Level 4: all P0 commands and mutations have CI-covered success and failure paths |
| ADR content quality | 2 | Five ADRs validate, but all omit decision makers and retrospective reconstruction is inconsistent | Level 4: RECORD contract, ownership, evidence separation, index stability, and confirmations are verified |
| Internationalization | 2 | Five index locales exist; prompts, templates, config, and non-ASCII title creation are incomplete | Level 4: eight locale catalogs plus INIT/CREATE/INDEX E2E, fallback, schema parity, and Unicode-title tests |
| CHECK correctness | 3 | Structural rules work; rename handling, ignored paths, and subprocess failure handling remain open | Level 4: no known false-confidence defect and all four evidence outcomes have regression coverage |
| Developer experience | 3 | Root README and executable quickstart exist; locale and config behavior are not documented or consistent | Level 4: repository config, override examples, and executable README commands are verified |
| Distribution parity | 2 | Four harness paths are documented, but only some were exercised end to end | Level 3: limitations are exact and every manifest has structural verification |
| Repository governance | 2 | Git Flow and CI exist; the private repository intentionally lacks enforceable branch rules | Level 3 before public through documented controls; Level 4 only after public rules are API-verified |
| Enterprise scalability | 1 | No organization ruleset, cross-repo catalog, RBAC, audit export, or adoption metrics | Remains post-v0.2.0; do not inflate the release scope |

The target is deliberately incremental. `v0.2.0` makes the local product and
its own ADRs trustworthy; it does not pretend to complete enterprise
governance in one release.

## v0.2.0 release scope and gates

The new locale set, repository configuration, and multilingual generation are
backward-compatible feature additions, so Semantic Versioning requires a minor
release (`v0.2.0`), not a patch release (`v0.1.1`).

### P0 — release blocking

- Non-ASCII-only and mixed-script titles create portable files reliably.
- The locale catalog, loader, and repository config resolution are
  deterministic.
- INIT, interactive CREATE, input CREATE, and INDEX support the canonical
  locale set.
- Runtime validation and JSON Schema remain consistent.
- Existing unreleased ADRs satisfy the minimum RECORD quality contract.
- CHECK has no known correctness defect that can produce false confidence.
- README documents repository defaults, per-command overrides, and executable
  examples for the released locale behavior.
- The full test suite and version-sync check pass freshly.

### P1 — strongly recommended before release

- Publish the Korean v0.2.0 readiness report.
- Add extended Korean and non-Latin quickstart examples.
- Improve dogfooding ADR content beyond the minimum contract where evidence is
  available.
- Reconcile `handoff.md`, `improvements.md`, and `project-roadmap.md`.

P1 work may move after the release only through an explicit owner decision
recorded in the readiness report; it must not silently disappear.

### P2 — post-release

- Apply public-repository GitHub governance after the visibility change.
- Add CODEOWNERS and review policy when more than one independent reviewer can
  satisfy it.
- Evaluate organization rulesets, enterprise adoption metrics, and
  cross-repository discovery from actual adoption evidence.

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
→ repository default
→ en
```

For standalone CLI workflows:

```text
explicit CLI --locale
→ locale supplied by an approved input draft
→ repository default
→ en
```

The standalone CLI does not guess from the operating-system locale. That would
make automation depend on the machine running it and would make CI output less
reproducible.

Argparse uses `None` for an omitted `--locale`; setting its parser default to
`en` would erase the distinction between an explicit CLI override and the
absence of one before repository configuration can be consulted.

### Repository configuration

The repository defines its normal ADR language once at its root:

```json
{
  "schema_version": 1,
  "locale": "ko"
}
```

The canonical filename is `.adr-toolkit.json`. JSON is selected instead of
YAML because the toolkit supports Python 3.9, has no YAML dependency, and must
not grow another incomplete hand-written YAML parser for two scalar settings.
TOML is not selected because `tomllib` is unavailable in Python 3.9's standard
library.

Commands resolve the file from the repository working directory. The README
continues to require running commands from the repository root. A malformed
config, unsupported `schema_version`, unknown field, or unsupported locale is a
visible configuration error rather than a silent English fallback.

INIT includes `.adr-toolkit.json` in its dry-run and creates it when absent,
using the explicit `--locale` or `en`. It never overwrites an existing config.
Existing repositories may add the small file directly; a dedicated config
mutation command is deferred until real usage shows that manual creation is a
problem.

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

The fallback is a safety net, not the preferred agent experience. In an agent
workflow, the agentic edge proposes a short semantic ASCII slug, shows it with
the title during CONFIRM, and supplies it to CREATE. The deterministic core
does not translate or transliterate; it only validates the supplied slug and
uses `decision` when no valid semantic slug exists.

```text
Korean title
→ agent suggests `separate-payment-system`
→ human approves title and slug
→ core validates `[a-z0-9-]+`
→ core writes `0006-separate-payment-system.md`
```

Standalone users may supply the same optional slug. This preserves useful file
navigation without introducing a nondeterministic translation library into the
core.

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

### Repository config loader

A focused config module loads `.adr-toolkit.json`, rejects unknown or malformed
state, and resolves locale precedence without writing files. INIT owns initial
config creation so config reads and mutations remain separate and testable.

### Template rendering

A focused template-rendering module converts locale strings and user-provided
answers into Minimal or Full MADR Markdown. Interactive CREATE and INIT call
this renderer rather than maintaining English prose inline. Agent-authored
draft bodies remain accepted as opaque approved Markdown.

### Command behavior

- `init --locale <code>` localizes generated files and records locale metadata.
- `create --interactive --locale <code> [--slug <ascii-slug>]` localizes
  prompts and structure and accepts an optional user-approved semantic slug.
- `create --input` accepts optional `locale` and `slug` draft fields; an
  explicit CLI locale overrides the draft locale.
- `index --locale <code>` keeps its existing responsibility and gains the
  three new locales.
- Omitted locale flags resolve through `.adr-toolkit.json` before falling back
  to English.
- `validate` checks a present locale, config validity, and all existing
  relationship invariants.

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

## CHECK confidence contract

CHECK validates explicit structural evidence; it never certifies an entire
architecture. The user-facing model distinguishes four meanings:

| Meaning | Interpretation |
|---|---|
| VERIFIED | Applicable deterministic rules were evaluated and no violation was found for this diff. |
| VIOLATED | Direct structural evidence proves that an explicit rule was violated. |
| UNVERIFIABLE | The ADR is relevant, but prose, missing rules, or ambiguous evidence prevents deterministic verification. |
| NOT_APPLICABLE | The ADR does not govern the changed scope. |

For backward compatibility, `v0.2.0` keeps the existing JSON finding kinds
(`related`, `review_required`, `verified_violation`, and
`no_applicable_constraint`). Documentation maps those kinds to the confidence
model and avoids calling an empty finding list “architecture verified.” A
future API normalization requires its own compatibility design.

The release-blocking correctness work is narrower and more urgent: rename
handling, ignored-path discovery, and every git subprocess failure must avoid a
false clean result. CHECK constraints are added to dogfooded ADRs only when the
rule vocabulary can prove the policy.

## Separate reports

Create:

```text
docs/adr-toolkit-v0.2.0-readiness-report.md
docs/enterprise-adoption.md
```

Both reports are Korean and distinguish four evidence classes:

1. Repository fact, linked to a file, test, command result, commit, PR, or
   workflow run.
2. External practice, linked to an official primary source.
3. Inference, explicitly labeled and tied to its evidence.
4. Recommendation, including priority, cost, dependency, and acceptance
   signal.

The readiness report stays release-focused:

- Executive assessment and maturity table.
- Product architecture and dependency boundaries.
- ADR dogfooding quality audit.
- `improvements.md`, `handoff.md`, and roadmap reconciliation.
- Reliability, security, portability, and developer-experience gaps.
- P0/P1 release gate evidence.
- Risks, invalidation triggers, and measurable success criteria.

The enterprise report owns the broader adoption path:

- Team ownership, proposal, review, acceptance, and exception workflow.
- Public GitHub transition checklist.
- CODEOWNERS, rulesets, required checks, and auditability.
- Organization-level governance, RBAC, taxonomy, and metrics.
- Cross-repository discovery and integration sequencing.

This split keeps enterprise analysis available without making every enterprise
capability appear to be part of `v0.2.0`.

## Work-tracking document boundaries

### `handoff.md`

Contains only the active task, touched files, next step, and open risk. Remove
the stale statement that the MVP feature branch is not integrated.

### `improvements.md`

Contains concrete implementation work selected for execution. Add the
repository config, localization, dogfooding corrections, reports, and CHECK
correctness work that have actionable `v0.2.0` acceptance criteria. Replace
umbrella links back to the roadmap with explicit tasks, owners or prerequisites,
priority, and a testable completion signal.

### `project-roadmap.md`

Contains unscheduled product bets. Remove items promoted to
`improvements.md`, including localized MADR headings and the concrete CHECK and
i18n/adapter/release follow-up lists. Keep genuine later bets such as semantic
conflict analysis, relationship visualization, multi-repo graphs,
public/enterprise governance automation, central portals, and external-system
integrations.

### Reports

Capture the assessment snapshot and why the priorities were chosen. They do not
become second task trackers.

## Post-v0.2.0 adoption boundary

The repository is private. Its current plan returns HTTP 403 for branch
protection and repository ruleset APIs. This is a platform-plan constraint and
an intentional pre-public state, not evidence that the documented Git Flow
policy was forgotten.

CI has run successfully on the first pull request and on `develop`, `master`,
and the release tag. The limitation is enforcement: GitHub cannot currently
prevent a direct push or an unreviewed merge. This does not block `v0.2.0`.

When the owner makes the repository public, the enterprise-adoption report
requires the operational task to apply and verify:

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
written only in `AGENTS.md` is not an enforcement signal. Team workflow, RBAC,
audit export, organization rulesets, metrics, and central discovery remain in
the separate enterprise report and post-release roadmap until usage evidence
promotes them into `improvements.md`.

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
- CLI accepts all eight locale codes and rejects unknown codes.
- Locale resolution proves CLI → draft → repository config → English
  precedence, including the agent-mediated precedence documented in SKILL.md.
- Missing config defaults to English; malformed, unknown-version, unknown-key,
  and unsupported-locale configs fail visibly.
- INIT dry-run reports config creation, INIT creates config when absent, and
  never overwrites an existing file.
- Each locale passes INIT → interactive CREATE → VALIDATE → INDEX in a scratch
  repository.
- Each generated body contains the expected localized headings.
- Non-ASCII-only, mixed-script, and explicit-slug titles create stable files.
- ADRs without locale remain valid; unsupported present locales fail.
- JSON Schema and runtime validation remain in parity.
- Agent guidance proposes an optional semantic ASCII slug and the core rejects
  invalid supplied slugs without attempting translation.

### Dogfooding and documentation

- All repository ADRs validate.
- The decision index regenerates without a diff.
- Confirmation claims are checked against actual files and commands.
- CHECK runs against a representative conforming and violating change.
- CHECK regression tests prove that rename handling, ignored paths, and every
  git subprocess failure cannot produce a false clean result.
- User documentation distinguishes verified rules from unverifiable policy and
  never equates an empty finding list with full architecture compliance.
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

1. Reconcile work-tracking documents and write the two assessment reports.
2. Implement repository config, locale resolution, and catalog completeness
   with tests.
3. Implement localized rendering boundaries across INIT, CREATE, and INDEX.
4. Implement portable slug fallback, semantic-slug input, and locale metadata
   with compatibility tests.
5. Update README, examples, agent guidance, and CHECK confidence language.
6. Correct the unreleased dogfooded ADRs and regenerate their index.
7. Fix release-blocking CHECK correctness defects selected in
   `improvements.md`.
8. Run every P0 verification signal and perform a final pre-`v0.2.0` review.
9. Complete or explicitly defer each P1 item in the readiness report.
10. After the repository becomes public, configure and API-verify GitHub
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
- Teams need repository config beyond locale and the minimal versioned JSON
  shape no longer covers a proven use case.
- Public or enterprise GitHub settings materially change the available
  enforcement model.
