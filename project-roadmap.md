# project-roadmap.md

Unscheduled product capabilities that need usage evidence or a separate design
before implementation. Concrete selected work belongs in `improvements.md`.

## Conflict detection depth

- Full semantic conflict taxonomy: Direct violation (for example, an SDK called
  directly where a Provider Port was decided) and Pattern divergence. This
  requires AST/import-graph analysis beyond deterministic path/dependency rules.
- Confidence scoring calibrated against a larger golden fixture set after real
  conflicts and false positives are available.
- Architecture fitness-function integrations that can verify richer policies
  without presenting heuristic guesses as proof.

## Harness parity

- Full cross-harness fixture/golden matrix for Codex, Gemini CLI, and
  Antigravity CLI at the depth currently available for Claude Code.
- Harness-specific hook support beyond Claude Code SessionStart when equivalent
  stable extension points exist.

## ADR navigation and scale

- Test whether 500+ decisions require sharding, alternate indexes, or a
  real search index (this repo has 10 ADRs; substring/tag/path matching is
  untested at that scale).
- Improve related-decision discovery beyond path/tag/keyword/body-substring
  only after real misses demonstrate the need for semantic retrieval.

## Internationalization

- Translate complete project documentation such as README and CONTRIBUTING
  after non-English contributors can review terminology and maintenance cost.
- Add Traditional Chinese as `zh-TW` only through a separate catalog and review;
  keep `zh` defined as Simplified Chinese.
- Evaluate bilingual ADR presentation only if teams need one decision rendered
  in more than one human language; do not create parallel sources of truth by
  default.

## Public and enterprise governance

- After the repository becomes public, apply and API-verify branch/tag
  protections, required checks, conversation resolution, force-push/deletion
  controls, and a documented bypass policy.
- Add CODEOWNERS and mandatory independent review when the contributor model can
  actually satisfy it.
- Organization-level rulesets, reusable workflows, RBAC, audit export,
  controlled taxonomy, exception governance, and adoption metrics.

## Ecosystem integration

- Pull-request review integration, initially as a GitHub Action and only later
  as a GitHub App if permissioned service behavior is justified.
- C4 / arc42 Section 9 export.
- Multi-repository decision discovery and graphing.
- Central decision portal or web viewer.
- Slack, Jira, and Notion integrations.
- Vector-backed semantic search after deterministic search has measured misses.

## Lifecycle research

- Revisit whether `retrospective` should become a first-class status rather than
  metadata after enough retrospective ADRs exist to show a lifecycle need.
- Define a narrow factual-correction policy for Accepted ADR metadata without
  weakening append-only decision history.
