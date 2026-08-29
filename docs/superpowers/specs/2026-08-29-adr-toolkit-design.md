# ADR Toolkit — MVP Design

- Status: Draft, pending user review
- Date: 2026-08-29
- Supersedes: none (first design doc)
- Source material: `adr-toolkit-prd.md` (v0.1 draft), plus brainstorming decisions in this session

## 1. Why this exists

The trigger for this project: Kafka was introduced into a production system,
and the person who made that decision is gone. Nobody left can say why Kafka
was chosen over the alternatives, what problem it solved, or what was
consciously traded away. Separately, AI coding agents now generate a large
share of new code, and by default they leave no trace of *why* a structural
choice was made — only the code itself.

ADR Toolkit exists to make sure that, going forward, the *reason* behind a
structural decision survives as long as the code does, is written by
inspecting the repository first (not invented), and is something a
successor — human or agent — can find in under a minute.

## 2. Goals (MVP)

1. Introduce an ADR system into an existing repository that has none, in
   under 10 minutes, by first inspecting code/config/git history for
   candidate past decisions.
2. Record a new decision by investigating relevant code and existing ADRs
   first, then asking the user only what the code cannot answer (max 3
   questions per round).
3. Check a git diff against existing Accepted ADRs for conservative,
   evidence-backed conflicts — false positives minimized over recall.
4. Keep every decision human-approved before it becomes "Accepted" — the
   agent proposes, the human decides.
5. Make ADRs easy to find as the collection grows: one flat directory, one
   auto-generated multi-view index.
6. Ship as one self-contained skill folder that works standalone, with thin
   per-harness adapters for Claude Code, Codex, Gemini CLI, and Antigravity
   CLI.
7. Localize the tool's own user-facing text (questions, reports, index
   section headers) into English, French, Japanese, Korean, and Chinese.
   ADR body content stays in whatever language the user answers in.
8. Build CI (tests, validation, release) from the first commit, not as a
   later add-on.

## 3. Non-goals (MVP)

Carried over from the PRD and still valid:

- No new ADR standard — reuse MADR 4.x.
- No web UI, SaaS, or hosted viewer.
- No C4/arc42/UML generation.
- No automatic code changes or rollbacks.
- No auto-approval of ADRs — a human always approves.
- No full semantic/AST-level conflict detection in MVP (see §7).
- No deep cross-harness fixture parity for Codex/Gemini CLI/Antigravity in
  MVP (see §8).
- No translation of ADR template section headers or project docs (README,
  CONTRIBUTING) in MVP (see §9) — only the skill's own runtime text.

Everything excluded here that still has value is tracked in
`project-roadmap.md`, not silently dropped.

## 4. Core principles (unchanged from PRD, restated)

- **Ask-after-Inspect** — investigate code, config, README, existing ADRs,
  and git diff before asking the user anything.
- **Human-owned Decisions** — the agent drafts and asks; only a human
  approves.
- **Evidence before Inference** — every claim about the "why" behind a past
  decision cites a code path, config, dependency, or existing ADR, or is
  explicitly labeled `retrospective`/inferred.
- **Deterministic Core, Agentic Edge** — file writes, ID assignment, index
  generation, and validation are deterministic scripts; significance
  judgment, interviewing, and drafting are the agent's job.
- **Harness-agnostic Core** — the skill works with no Claude-specific env
  vars or hooks; hooks are optional notification only.
- **No Silent Mutation** — every ADR creation, status change, or supersede
  is shown to the user as a plan before it is written.

## 5. Repository structure

```text
adr-toolkit/
├── skills/
│   └── adr-toolkit/                  # the entire distributable unit
│       ├── SKILL.md
│       ├── VERSION
│       ├── scripts/
│       │   ├── adr.py                # single CLI entrypoint, subcommand dispatch
│       │   ├── commands/
│       │   │   ├── preflight.py
│       │   │   ├── discover.py
│       │   │   ├── init.py
│       │   │   ├── create.py
│       │   │   ├── index.py
│       │   │   ├── validate.py
│       │   │   ├── diff.py
│       │   │   ├── related.py
│       │   │   └── check.py
│       │   ├── core/                 # id calc, frontmatter model, lifecycle rules
│       │   ├── evidence/             # dependency/git/code-comment/entrypoint scanners
│       │   ├── rules/                # significance scoring + conflict rules (data-driven)
│       │   └── i18n/
│       │       ├── en.json
│       │       ├── fr.json
│       │       ├── ja.json
│       │       ├── ko.json
│       │       └── zh.json
│       ├── templates/
│       │   ├── madr-minimal.md
│       │   └── madr-full.md
│       ├── references/               # loaded on demand, not always in context
│       │   ├── significance-rules.md
│       │   ├── interview-guide.md
│       │   ├── conflict-rules.md
│       │   ├── lifecycle.md
│       │   └── madr-guide.md
│       └── schemas/
│           └── adr.schema.json
├── adapters/                          # per-harness glue only; no business logic here
│   ├── claude/
│   │   ├── .claude-plugin/plugin.json
│   │   ├── marketplace.json
│   │   └── hooks/
│   │       ├── hooks.json
│   │       └── session_start.py
│   ├── codex/
│   │   └── .codex-plugin/plugin.json
│   ├── gemini-cli/
│   │   └── gemini-extension.json
│   └── antigravity/
│       └── antigravity-plugin.json
├── docs/
│   └── decisions/                     # adr-toolkit dogfoods itself
│       ├── README.md                  # auto-generated multi-view index
│       ├── adr-template.md
│       └── 0001-adopt-architecture-decision-records.md
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── behavioral/
│   ├── fixtures/
│   └── golden/
├── project-roadmap.md
├── AGENTS.md / CLAUDE.md / CODEX.md / GEMINI.md
├── README.md / CHANGELOG.md / LICENSE
└── .github/workflows/
    ├── test.yml
    └── release.yml
```

Rationale for `adapters/` living at the repo root instead of nested under
each harness's own convention folder (e.g. `.claude-plugin/` at root): it
makes "the product" (`skills/`) and "how a harness plugs into the product"
(`adapters/`) visually and structurally separate. Adding a fifth harness
later means adding one folder under `adapters/`, never touching `skills/`.

## 6. ADR document format

Unchanged from the PRD's model (§11), reconfirmed here:

- Flat directory: `docs/decisions/NNNN-kebab-case-title.md`, 4-digit
  zero-padded, IDs never reused, superseded files kept.
- Every file has three fixed blocks: YAML frontmatter (machine-readable:
  id, title, status, date, related, affected_paths, tags, retrospective),
  the MADR body (Minimal or Full, chosen automatically by the skill based on
  option count and quality-attribute conflict), and an Agent extension
  section (Affected Code, Implementation Constraints, Verification
  checklist) that CHECK later reads.
- The Agent extension's `Implementation Constraints` list is the contract
  CHECK compares diffs against — plain-language rules like "feature modules
  must not import provider SDKs directly," matched by path/import evidence,
  not free-form semantic reasoning.

## 7. CHECK scope for MVP: conservative, evidence-only

The PRD's 8-type conflict taxonomy (§9.4) requires semantic understanding
of code intent for at least two types (Direct violation, Pattern
divergence) that cannot be reliably detected without deep static analysis.
Shipping that unverified in an MVP risks false positives on day one, which
is the fastest way to lose trust in a brand-new open-source tool.

MVP CHECK is restricted to conflict types where the evidence is structural,
not semantic:

| Type | MVP detection method |
|---|---|
| Dependency conflict | New dependency name matches something a `superseded`/`rejected` ADR named as rejected. |
| Boundary / path violation | Changed file path falls under an ADR's `affected_paths`, and the diff touches an import/call listed in that ADR's `Implementation Constraints`. |
| Missing realization | An ADR's `Verification` checklist item references a path/test that the diff removes or never created. |
| Superseded reference | New code imports/references a path or package explicitly named in a `superseded` ADR's decision. |

Everything else from the original taxonomy (Direct violation via SDK-call
detection, Pattern divergence) moves to `project-roadmap.md` pending a
proper AST/import-graph based approach. Findings without direct structural
evidence are reported at `Info` severity ("possible related ADR, no direct
conflict evidence") rather than `Major`/`Critical`.

## 8. Harness support strategy

Four harnesses are in scope for MVP, at two different depths:

| Harness | MVP depth |
|---|---|
| Claude Code | Full: plugin manifest, optional SessionStart hook, fixture + golden tests, primary development/dogfooding target. |
| Codex | Adapter manifest present and manually verified to install and run INIT/RECORD/CHECK once end-to-end. No fixture matrix. |
| Gemini CLI | Same as Codex. |
| Antigravity CLI | Same as Codex. |

Because the skill itself is harness-agnostic (no Claude-specific env vars,
relative-path resolution only), a harness needs nothing more than a
manifest pointing at `skills/adr-toolkit/` to work. Full cross-harness
fixture parity testing for the three secondary harnesses is deferred to
`project-roadmap.md`.

## 9. Internationalization scope

Only the skill's own runtime output is localized for MVP: the questions it
asks, the report text (discovered facts, findings, confidence), and the
generated index's section headers (by status / by tag / by affected path).
Supported locales: `en`, `fr`, `ja`, `ko`, `zh`, stored as flat key→string
JSON files under `scripts/i18n/`. Locale selection follows the user's
request language when detectable, defaulting to `en`.

Not in MVP scope: translated MADR template section headers (the template
stays in English section names regardless of locale — content is whatever
language the user writes), and translated project documentation
(README/CONTRIBUTING). Both are `project-roadmap.md` candidates once the
project has real non-Korean/English contributors to validate against.

## 10. Multi-view index

`scripts/commands/index.py` regenerates `docs/decisions/README.md` after
every create/status-change. It is one flat file with multiple generated
views, not a nested directory tree — nesting real folders was rejected
because it fragments ID uniqueness and breaks `related`/`supersedes` links
across folder boundaries as ADRs get recategorized. The views:

- By status (Accepted / Proposed / Rejected / Deprecated / Superseded)
- By tag
- By affected path (so "what decisions touch `src/events/`" is a lookup,
  not a grep)
- Reverse chronological

This delivers the "fast, structured lookup" goal without the fragility of a
real hierarchical file tree.

## 11. Workflow data flow

### INIT

```text
preflight --json
  → discover --json            (deps, docker/k8s, entrypoints, git log, code comments)
  → [significance rules]       classify candidates High/Medium/Low
  → [interview planner]        ask only what evidence can't answer, ≤3/round
  → [drafter]                  retrospective MADR draft per approved candidate
  → user approval gate
  → init --dir docs/decisions  (scaffold directory + template + ADR-0001)
  → create --input draft.json  (per approved candidate)
  → validate --json
  → index                      (regenerate README.md)
```

### RECORD

```text
[router matches record intent]
  → related --paths <affected> --json
  → [significance scoring, 0–14 scale per PRD §8.3]
  → score ≤3 → recommend against an ADR, point to commit message/code comment instead
  → score ≥4 → ask ≤3 questions (locale-aware) → draft MADR (minimal or full)
  → user approval gate (title/problem/options/decision/driver/downside/affected paths shown)
  → next-id --json → create --input draft.json
  → validate --json → index
```

### CHECK

```text
diff --since <ref> --json      (uncommitted / staged / branch / commit range)
  → classify changed files      (new dependency, new entrypoint, changed import)
  → related --paths <changed> --json
  → [conservative conflict rules, §7]  structural evidence only
  → Finding report (severity + evidence + confidence)
  → intentional decision change? → recommend Supersede + RECORD
  → otherwise → recommend reverting to the existing decision
```

## 12. Testing & CI (built from day one)

MVP includes, not defers:

- Unit tests: ID calculation, frontmatter validation, lifecycle transitions,
  index generation, git diff parsing.
- Integration tests: empty-repo INIT, existing-MADR-repo detection,
  Nygard-format preservation, RECORD-then-reindex, supersede relationship.
- Behavioral tests: no re-asking facts evidence already answered, ADR
  refused for non-architectural changes, ≤3 questions enforced, no file
  writes before approval.
- Fixtures + golden results for the Claude Code harness (per PRD §20.5–20.6).
- `.github/workflows/test.yml` runs all of the above on every PR.
- `.github/workflows/release.yml` handles version sync, tagging, and
  GitHub Release once tests pass.

## 13. Decisions resolved during this session

These were open items in the PRD's §28 ("미해결 결정") or newly raised;
resolving them here so they don't block implementation:

| Item | Resolution |
|---|---|
| CLI as a separate product? | No — scripts are an internal implementation detail. The skill is the primary interface and calls scripts internally. |
| Python stdlib only? | Yes, confirmed (already implied by PRD §15.3). |
| Directory structure for scale | Flat directory + auto-generated multi-view index, not nested folders (§10). |
| CHECK depth for MVP | Structural/evidence-based only; full semantic taxonomy deferred (§7). |
| Harness priority | Claude Code deep, Codex/Gemini CLI/Antigravity CLI light adapters (§8). |
| i18n scope | Skill runtime text in 5 languages; templates/docs not translated in MVP (§9). |
| License | MIT, proposed here for user confirmation on return — matches the PRD's own lean (§27.1) and is the least-friction choice for the stated goal of broad adoption/stars. Needs explicit sign-off before the repo goes public. |

## 14. What's deferred to `project-roadmap.md`

- Full semantic conflict taxonomy (Direct violation, Pattern divergence)
  via AST/import-graph analysis.
- Full cross-harness fixture/golden parity for Codex, Gemini CLI,
  Antigravity CLI.
- ADR relationship graph visualization.
- Localized MADR template section headers.
- Localized project documentation (README, CONTRIBUTING) in 5 languages.
- PR review integration / GitHub App / automated PR comments.
- ArchUnit-style static enforcement integration.
- C4/arc42 export.
- Multi-repo decision graph, vector DB, central decision portal.
- Slack/Jira/Notion integrations.

## 15. Success criteria (MVP)

Carried from PRD §22.3, scoped to what MVP actually attempts:

- INIT completes in under 10 minutes on an ADR-less fixture repo.
- 100% of generated ADRs pass structural validation (ID, frontmatter,
  required sections, links, index consistency).
- Zero files written before an explicit user approval.
- Zero re-asked questions for facts already visible in code/config/existing
  ADRs, measured against fixtures.
- Zero citations of nonexistent ADR IDs or file paths.
- All three workflows (INIT/RECORD/CHECK) run correctly on Claude Code
  against the fixture set; Codex/Gemini CLI/Antigravity CLI each run the
  three workflows once, manually verified, without full fixture coverage.
- The `skills/adr-toolkit/` folder, copied alone into a fresh location,
  passes its own test suite.
