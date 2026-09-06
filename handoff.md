# handoff.md

## Current task

Cline harness entry file (`CLINE.md`) added and `AGENTS.md` updated to list
Cline alongside Codex/Claude/Gemini, plus an explicit per-model non-creation
policy (`DEEPSEEK.md`/`GLM.md`/`KIMI.md`/`QWEN.md` are not created — those are
model/API providers routed through a harness such as Cline, not harnesses).

## Touched files

- `CLINE.md` — new thin harness entry pointer (matches `CODEX.md`/`CLAUDE.md`/
  `GEMINI.md` shape) with Cline-specific notes: open Agent Skills discovery,
  no adapter-local manifest, and the verified AGENTS.md auto-injection
  behavior.
- `AGENTS.md` — added `Cline` to the harness enumeration (line 4) and added
  `CLINE.md` to the harness entry-files list (line 69), plus a paragraph
  stating per-model entry files are intentionally not created.
- `tests/unit/test_cline_adapter.py` — added
  `test_cline_entry_file_is_thin_pointer_to_agents_md` and
  `test_agents_md_lists_cline_among_harnesses`.
- `changelog.md` — one Unreleased line.
- `handoff.md` — this file.

## Diagnosis / empirical verification

Confirmed via an isolated Cline run that Cline auto-injects the repo-root
`AGENTS.md` into workspace context at session start:

```
cline --data-dir <mktemp -d> --json 'Output ONLY the literal first line of
this repository AGENTS.md file. Do not run any tools...'
→ reasoning: "Looking at the Workspace Configuration, I see the full content
   of the AGENTS.md file was provided in the workspace context."
→ text: "# AGENTS.md"
→ model: cline-pass/glm-5.2
```

So `AGENTS.md` already reaches every model routed through ClinePass
(DeepSeek, GLM, Kimi, Qwen, …). Per-model entry files would be redundant
because the harness (Cline) is the layer that owns project-context injection.

## Next step

1. (This PR) `docs/cline-harness-entry` → `develop` via PR #37; wait for CI
   (13 checks, same matrix as PR #36).
2. (Future, already logged in PR #36) Implement the Medium backlog item to
   fold Cline into the `harness-parity` CI job.

## Verification

- `tests/unit/test_cline_adapter.py`: 5 cases (3 original + 2 new) — re-run
  with Python 3.13 standalone.
- `git diff --stat`: 5 files, all markdown + test — ruff/mypy scope:
  `test_cline_adapter.py`.

## Open risks

- Cline auto-injection of `AGENTS.md` was verified on Cline CLI 3.0.61 with
  `cline-pass/glm-5.2`; behavior may differ on other Cline versions or
  providers. The Medium harness-parity CI backlog item (PR #36) covers
  ongoing regression detection once implemented.
- Inherits Open risks from the prior handoff (ruleset context sync,
  `continue-on-error` PyPI publish, deferred issue/PR automation).
