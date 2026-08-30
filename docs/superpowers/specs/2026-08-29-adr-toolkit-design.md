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
- The Agent extension's `Implementation Constraints` section carries prose
  for human readers **plus** an optional fenced `constraints:` YAML block
  for CHECK to parse deterministically (see §7 — free-form prose alone
  cannot be checked deterministically, which would violate the
  Deterministic Core principle).
- A retrospective ADR (`retrospective: true`) additionally requires three
  explicitly separated subsections in its body, never merged into one
  narrative: **Confirmed Evidence** (only facts the discover step or the
  user's own words established), **Inferred Rationale** (the agent's best
  guess, clearly labeled as a guess), and **Unknown** (anything about the
  original decision that cannot be recovered from this repository). This
  makes Evidence-before-Inference (§4) checkable by a reader, not just a
  stated principle — a direct response to the motivating case of a
  decision-maker leaving with no record of their reasoning.

### 6.1 What belongs in an ADR

Not every structural-looking change deserves a new file. CLASSIFY (used by
INIT, DISCOVER, and RECORD alike) applies this table before drafting
anything:

| Content | Where it belongs |
|---|---|
| Structural, long-lived decision | ADR |
| Feature implementation detail | Pull request |
| Routine code-change rationale | Commit message |
| Usage/behavior explanation | README or docs |
| Incident/outage response | Incident report / postmortem |
| A rule that must hold going forward | ADR's Implementation Constraints |

Treating "record this feature" and "record the structural decision inside
this feature" as the same request is the single most likely way this tool
degrades into a changelog generator — CLASSIFY exists specifically to
prevent that.

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
proper AST/import-graph based approach.

**Structured constraints, not prose matching.** The `Implementation
Constraints` section of an ADR (§6) may carry a fenced `constraints:` YAML
block using a small fixed vocabulary of checkable rule kinds:

```yaml
constraints:
  - id: no-provider-sdk-in-feature
    kind: forbidden_import
    paths: ["src/features/**"]
    pattern: ["openai.*", "anthropic.*"]
    severity: major
    message: "Feature modules must use the LLM port."
```

MVP supports `forbidden_import`, `required_path`, `forbidden_path`,
`dependency_forbidden`, `file_must_exist`, `test_must_exist`. CHECK matches
diffs against these structurally; it never attempts to interpret
free-form English constraint prose as an enforceable rule. An ADR with no
`constraints:` block simply has nothing CHECK can mechanically enforce for
it — that's a legitimate state, not an error.

**Four-way finding classification**, replacing plain severity levels for
clearer signal about what a human actually needs to do:

| Classification | Meaning |
|---|---|
| Related | The diff touches a path an ADR names, no rule fired. |
| Review required | A rule-less ADR judgment call — needs a human look, not a mechanical yes/no. |
| Verified violation | A `constraints:` rule fired with direct structural evidence. |
| No applicable constraint | An ADR covers this path but has no `constraints:` block. |

When CHECK reports a `Verified violation`, it offers the user a choice
rather than defaulting to "revert the code": (1) fix the code to match the
existing ADR, (2) supersede the ADR with a new decision, (3) narrow or
widen the ADR's `affected_paths`/`constraints`, (4) register a documented
exception, or (5) mark it a false positive. This work is planned for Plan
3 (CHECK), not implemented in Plan 1.

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

**Generic fallback, restored.** The Codex/Gemini CLI/Antigravity adapter
manifests above rest on each harness's assumed plugin/skill discovery
format, which hasn't been verified against real documentation for any of
the three. To make sure the tool works even if those assumptions are wrong
— and for any harness not on this list at all, present or future — a
`adapters/generic/` fallback (present from Plan 1, not deferred) documents
a manual install: symlink `skills/adr-toolkit/` into the target repo and
add one line to that repo's `AGENTS.md` pointing at its `SKILL.md`.
`SKILL.md` only assumes markdown-reading and shell execution, so this
fallback has no dependency on any harness-specific convention being right.

**Usable with no AI agent at all.** `create` also gains an `--interactive`
mode (Plan 1) that prompts the same questions a skill would ask, directly
in the terminal, and writes the ADR without any JSON draft file or agent
involvement. Without this, the tool is only natural for agent-mediated
use, which cuts against the stated goal of easy adoption by developers who
try it standalone before ever wiring up a harness.

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

INIT and past-decision recovery are two separate user-facing operations,
not one bundled flow — a repository can be initialized without immediately
mining its history, and history mining can be re-run later on an
already-initialized repository.

### INIT (scaffolding only)

```text
preflight --json              (stop if existing_adr_directory is already set)
  → user confirms the directory that will be created
  → init --dir docs/decisions  (scaffold directory + template + ADR-0001)
  → validate --json
  → index                      (regenerate README.md)
```

### DISCOVER (past-decision recovery, independently invokable)

```text
preflight --json               (must already have an ADR directory — tell the user to run INIT first if not)
  → discover --json            (deps, docker/k8s, entrypoints, git log, code comments)
  → [classify]                 structural vs. routine, using the "what belongs in an ADR" table (§6)
  → [interview planner]        ask only what evidence can't answer, ≤1 question per candidate
  → [drafter]                  retrospective MADR draft per approved candidate, with the
                                mandatory Confirmed Evidence / Inferred Rationale / Unknown split (§6)
  → user approval gate         (per candidate — any can be dropped)
  → create --input draft.json  (per approved candidate)
  → validate --json
  → index
```

### RECORD

RECORD is not limited to decisions made *before* implementation. It equally
supports capturing a decision that was made *during* or *just after*
implementing a feature (e.g. "find what in this branch should become an
ADR") — the workflow is identical, only the trigger differs (a user
request vs. a diff/branch range instead of a forward-looking question). Not
every change in a diff is ADR-worthy; RECORD applies the same "what belongs
in an ADR" table (§6) before drafting anything.

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

### Lifecycle operations (status changes, supersede, deprecate)

Not implemented in Plan 1 (which only ever creates status `accepted` for
ADR-0001 and whatever status a draft specifies at creation time). Plan 2
adds explicit user-facing triggers and matching deterministic script verbs,
enforced by `core.lifecycle.validate_transition` (already built in Plan 1):

```text
"이 ADR을 승인 상태로 변경해줘"       → adr.py status 0012 --to accepted
"ADR-0012는 ADR-0021로 대체됐어"     → adr.py supersede 0012 --by 0021
"이 결정은 더 이상 적용되지 않아"     → adr.py deprecate 0012
```

The agent may show the user a change plan, but the script only writes the
new status after explicit user approval — same No Silent Mutation rule as
`create`.

### CHECK

```text
diff --since <ref> --json      (uncommitted / staged / branch / commit range)
  → classify changed files      (new dependency, new entrypoint, changed import)
  → related --paths <changed> --json
  → [structured constraint rules, §7]  match constraints: blocks only
  → Finding report: Related / Review required / Verified violation / No applicable constraint (§7)
  → for a Verified violation, present the 5 resolution options from §7
    (fix code / supersede / narrow-or-widen the ADR / register exception / false positive)
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
| INIT vs. history recovery | Split into two independently invokable operations — INIT (scaffolding only) and DISCOVER (past-decision mining) — instead of one bundled flow. Added after user feedback; see §11. |
| Implementation Constraints format | Structured `constraints:` YAML block with a fixed rule-kind vocabulary, not free-form prose — prose alone can't be checked deterministically. Added after user feedback; see §6.1 and §7. |
| Retrospective ADR body structure | Must separate Confirmed Evidence / Inferred Rationale / Unknown into distinct subsections, never merge into one narrative. Added after user feedback; see §6. |
| CHECK finding classification | Four-way (Related / Review required / Verified violation / No applicable constraint) plus 5 resolution options on a verified violation, replacing a plain severity scale. Added after user feedback; see §7. |
| Harness fallback | Restored a generic, manifest-free fallback adapter (symlink + one `AGENTS.md` line) dropped when the harness list was narrowed to four named ones — de-risks the Codex/Gemini CLI/Antigravity manifests being unverified guesses. Built in Plan 1, not deferred; see §8. |
| Human usability without an agent | `create --interactive` terminal wizard added to Plan 1 so the tool has a natural, complete experience for a developer with no AI harness at all, not only for agent-mediated use; see §8. |

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

## 16. Plan 3 (CHECK) implementation decisions

Resolved during Plan 3 brainstorming, in the same spirit as §13 — these fill
gaps §7 and §11 leave open at the product-design level, without changing
either section's MVP boundary.

### 16.1 Module split

- `scripts/commands/diff.py` — wraps `git diff` via `subprocess` for three
  modes (`--staged`, `--uncommitted`, `--since <ref>` diffing `<ref>..HEAD`).
  Returns per-file entries with both the changed path and the actual added
  line content (`{path, change_type, added_lines, removed_lines}`), because
  content-pattern rules (below) need to see *what* was added, not just
  *which file* changed.
- `scripts/rules/conflict.py` — pure functions taking a parsed diff plus
  `(adr_data, constraints)` pairs, returning findings. No file or git I/O,
  mirroring the existing `scripts/rules/significance.py` split so the
  matching logic stays unit-testable in isolation.
- `scripts/commands/check.py` — orchestrates: calls `diff.run()`, scans
  Accepted ADRs for `affected_paths` overlap (reusing `related.py`'s
  overlap logic), scans Superseded ADRs separately for the
  superseded-reference check, calls `rules/conflict.py`, and assembles the
  four-way finding report.

### 16.2 Constraint-matching semantics

The six `constraints:` rule kinds collapse into four deterministic,
glob/regex-only mechanisms — no per-language import parsing, no
dependency-manifest-format parsing:

| Mechanism | Kinds | Fires when |
|---|---|---|
| Content pattern in diff | `forbidden_import`, `dependency_forbidden` | An added line in a file matching `paths` (glob) matches any regex in `pattern`. `dependency_forbidden` is mechanically identical to `forbidden_import`; the distinction is purely which paths (e.g. manifest files) the ADR author scopes it to. |
| Required companion path | `required_path` | The diff touches a file matching `paths`, but no file matching `pattern` (glob) is touched by the diff or already exists in the working tree. |
| Forbidden companion path | `forbidden_path` | The diff touches a file matching `paths` AND also touches a file matching `pattern` (glob). |
| Existence check | `file_must_exist`, `test_must_exist` | None of the paths matching `paths` (glob) exist in the working tree after the diff. Identical mechanism for both; `test_must_exist` is a semantic label for the ADR author, not different logic. |

A small `**`-aware glob-to-regex translator is added under `core/` (stdlib
`fnmatch`/`PurePath.match` don't handle `**` well), reusable by future
`related.py` path matching too.

### 16.3 Four-way classification algorithm

For each Accepted ADR whose `affected_paths` overlaps the diff, two checks
run independently (an ADR can produce more than one finding):

1. **Constraints evaluation** — only if the ADR has a `constraints:` block:
   run every rule via §16.2's mechanisms. Any rule that fires → `Verified
   violation`. Block exists but nothing fires → `Related`.
2. **Missing-realization heuristic** — always runs regardless of a
   `constraints:` block: scans the ADR body's `Verification` checklist
   section for path/test-like tokens; if the diff removes one or it was
   never created → `Review required`. This is prose-scanning, not a
   `constraints:` rule, so it is capped at `Review required` rather than
   `Verified violation` even though the check itself is mechanical — it
   isn't backed by the same structured evidence the other rule kinds are.

If neither check produces anything and the ADR has no `constraints:` block
at all → `No applicable constraint`.

**Superseded reference** is a separate pass: for each *Superseded* (not
Accepted) ADR, reuse `related.py`'s `affected_paths` overlap check only —
not that ADR's old `constraints:` block, since a superseded ADR's rules are
no longer "in force" as enforceable evidence. Any overlap → `Verified
violation`, `kind: superseded_reference`, pointing at both the old ADR and
its `superseded_by` target.

Every `Verified violation` (from `constraints:` or from
`superseded_reference`) carries the fixed 5-option `resolutions` array from
§7 (fix code / supersede / narrow-or-widen / register exception / false
positive) as static text, not computed per finding.

### 16.4 Constraints scope

`constraints:` rules are evaluated only against ADRs with `status:
accepted`, matching `lifecycle.md`'s existing "currently in force"
language. Proposed/rejected/deprecated ADRs impose no enforceable
constraints; superseded ADRs are handled by the separate
superseded-reference pass in §16.3, not by re-running their constraints.

### 16.5 `diff` CLI shape

`git diff`-style flags rather than a single raw range argument:
`--staged`, `--uncommitted` (booleans for those two modes), `--since <ref>`
(diffs `<ref>..HEAD`). Mirrors familiar `git diff` semantics instead of
requiring the caller to construct raw revision syntax.

### 16.6 Output shape and error handling

`check`'s JSON output follows the existing `related`/`validate` convention:

```json
{
  "ok": true,
  "operation": "check",
  "diff": {"mode": "since", "ref": "main", "files_changed": 4},
  "findings": [
    {"adr_id": "ADR-0007", "kind": "verified_violation", "rule_id": "no-provider-sdk-in-feature",
     "severity": "major", "file": "src/features/x.py", "message": "...",
     "evidence": {"line": "import openai", "pattern": "openai.*"},
     "resolutions": ["fix_code", "supersede_adr", "adjust_scope", "register_exception", "false_positive"]},
    {"adr_id": "ADR-0003", "kind": "related"},
    {"adr_id": "ADR-0012", "kind": "review_required"},
    {"adr_id": "ADR-0002", "kind": "no_applicable_constraint"}
  ],
  "warnings": []
}
```

Error handling follows the pattern the Plan 2 closeout review established:
malformed ADR frontmatter is caught per-file and degrades to a `warnings`
entry rather than aborting the whole `check`; a `diff` failure (not a git
repo, unknown ref) returns a specific code (`NOT_A_GIT_REPO`,
`INVALID_REF`) rather than surfacing a raw `subprocess` traceback through
`main()`'s `INTERNAL_ERROR` fallback.

### 16.7 Testing strategy

- `rules/conflict.py`'s 4 mechanisms: pure unit tests against synthetic
  diff dicts, no git or filesystem — mirrors `test_significance.py`.
- `diff.py`: unit tests against real `tmp_path` git repos (init, commit,
  diff), since it is the one new module that actually shells out to git.
- `check.py`: integration tests combining a fixture repo with an Accepted
  ADR carrying a `constraints:` block plus a violating diff, plus a golden
  test extending `tests/integration/` for a CHECK-only flow — flag a
  violation, fix the code, confirm the violation clears.

## 17. Plan 4 (i18n, adapters, release) implementation decisions

Resolved during Plan 4 brainstorming, in the same spirit as §13 and §16.
Both open decisions from §13 are now closed: **license is MIT** (a
`LICENSE` file already exists at repo root from the initial commit), and
**final MVP scope keeps the original five languages and four harnesses** —
no scope trim.

### 17.1 i18n scope and mechanism

The only deterministic, code-owned user-visible text in the toolkit is
`index.py`'s generated `README.md` (section headers, status labels).
Everything else RECORD/DISCOVER/CHECK surface to the user — interview
questions, findings reports, summaries — is composed fresh by the agent
each time following `SKILL.md`, and an LLM is already multilingual; it
needs no phrase-book to ask a question in French. Treating agent-composed
prose as an i18n target would mean building and maintaining a translation
table for text that was never fixed-string in the first place.

- `scripts/i18n/{en,fr,ja,ko,zh}.json` — flat key→string files holding
  *only* `index.py`'s generated strings (section headers like "By status",
  status labels like "Accepted"). This is the only place a JSON lookup
  table earns its keep.
- `index.py` gains a `--locale` flag (default `en`). It loads the matching
  JSON file; a missing file or a missing key within it falls back to the
  `en` value for that key (never a raw key name or a crash) — a repo
  should never lose its index because a translation is incomplete.
- `SKILL.md` gains one instruction, not a lookup table: detect the user's
  language from their request and compose questions/reports in it
  (default English), and pass the same locale to `index --locale <code>`.
  This preserves the "Deterministic Core, Agentic Edge" split (§4) — the
  script never guesses a language, the agent always does.
- Explicitly out of scope: `adr.py`'s `--json`-always-emits-JSON standing
  risk (tracked in `handoff.md`) is untouched by Plan 4 — locale affects
  only the string *content* `index.py` writes to `README.md`, not the CLI's
  JSON transport contract.

### 17.2 Harness adapters — verified formats, not inferred

Plan 1's Claude Code adapter guessed a `"skills"` key and a nested manifest
path that turned out wrong, caught only by its final review. Plan 4 does
not repeat that: each format below was looked up against real
documentation during Plan 4's brainstorming, not inferred from Claude
Code's adapter.

| Harness | Manifest | Required fields | Notes |
|---|---|---|---|
| Codex CLI | `.codex-plugin/plugin.json` | `name` (optionally `$schema`) | Follows the cross-vendor **Agent Plugins 1.0.0** standard (Amazon/Anysphere/Microsoft/OpenAI/Vercel, released 2026-08-06); Codex's implementation shipped 2026-08-07 — very recent, worth re-verifying against `github.com/agentplugins/agent-plugins-spec` if this drifts before Plan 4 implements. |
| Gemini CLI | `gemini-extension.json` | `name` (optionally `version`, `description`, `contextFileName`) | |
| Antigravity CLI | `plugin.json` | `name` (optionally `description`, `$schema` pointing at `https://antigravity.google/schemas/v1/plugin.json`) | |

All three documented examples show `skills/` as a subdirectory of the
manifest's own location, not an externally-pointed path — no field in any
of the three schemas lets a manifest reference a skill directory
elsewhere. Since the toolkit's actual skill is the single self-contained
`skills/adr-toolkit/` package (the whole point of Plan 1), each adapter
gets a **symlinked** `skills/adr-toolkit` under its own directory
(`adapters/codex/skills/adr-toolkit -> ../../../skills/adr-toolkit`, and
equivalently for the other two) — the same pattern
`adapters/generic/README.md` already documents for manual installs, never
a duplicated copy of the package.

**Manual end-to-end verification, not just schema tests**, per §8's
already-stated depth ("manually verified to install and run
INIT/RECORD/CHECK once end-to-end"). `codex` (0.151.0) and `gemini`
(0.46.0) CLIs are present in this development environment, so their
adapters can get a real install-into-a-scratch-repo-and-run verification
during implementation. No `antigravity` CLI is available here — that
adapter's task is scoped to structural/schema validation only, with the
limitation stated plainly in its task report rather than a false claim of
end-to-end verification.

### 17.3 Version synchronization and release automation

Version currently lives in three places already (`skills/adr-toolkit/VERSION`,
`.claude-plugin/plugin.json`'s `"version"` field, `SKILL.md`'s frontmatter
`version:` field). Of the three new adapter manifests, only Gemini's
`gemini-extension.json` documents an optional `version` field in its
schema; Codex's and Antigravity's minimal examples in §17.2 don't show
one (their schemas may support it without it appearing in the examples
found — confirm during implementation rather than assuming either way).

- `skills/adr-toolkit/VERSION` remains the single source of truth.
- A new `scripts/sync_version.py` at the repo root (tooling for the repo
  itself, not part of the distributable `skills/adr-toolkit/` package, so
  it lives outside that directory) reads `VERSION` and writes it into
  every manifest confirmed to carry its own `version` field — checking
  each new adapter manifest for one during implementation rather than
  assuming all four need it. A `--check` mode reports drift without
  writing, exit code 1 if anything would change.
- `.github/workflows/test.yml` gains a step running
  `python scripts/sync_version.py --check` — a forgotten version bump on
  any manifest fails CI on every PR, not just at release time.
- New `.github/workflows/release.yml`, triggered on a version-tag push
  (`v*`): runs the full test suite, then creates a GitHub Release with
  the changelog. It does not auto-bump the version — a human bumps
  `VERSION`, runs `sync_version.py` (no `--check`) to propagate it,
  commits, and pushes the tag; the workflow's job is packaging and
  publishing an already-decided release, not deciding when to cut one.

### 17.4 Testing strategy

- i18n: unit tests that `index.py --locale <code>` renders each locale's
  strings correctly, that a missing locale file falls back to English
  content (not a crash or a raw key), and that a locale file missing one
  key falls back to English for just that key.
- Adapters: a structural/schema test per manifest (valid JSON, required
  fields present, matches the documented schema) for all four adapters;
  a manual end-to-end install-and-run report (not an automated pytest
  case — no CI runner here has `codex`/`gemini`/`antigravity` installed)
  for Codex and Gemini, explicitly noting Antigravity's is unverified.
- Version sync: unit tests for `sync_version.py`'s `--check` mode
  (detects drift, exits non-zero) and its write mode (updates every
  tracked manifest correctly), run against fixture copies of each
  manifest file, not the real repo files.
- Release workflow: no automated test (GitHub Actions workflows aren't
  unit-testable in this repo's stack); reviewed by reading the YAML
  against `test.yml`'s existing conventions.
