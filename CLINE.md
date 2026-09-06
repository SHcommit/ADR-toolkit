# CLINE.md

Follow the shared project rules in `AGENTS.md` first.

Use this file only for Cline-specific notes that cannot live in the shared
document.

## Cline-specific notes

Cline discovers this project as **Project Skill** via the open Agent Skills
standard (`skills/adr-toolkit/SKILL.md`); see `adapters/cline/README.md` for
install details. Unlike Codex/Gemini/Antigravity, Cline has no adapter-local
manifest — the canonical `SKILL.md` frontmatter (`name: adr-toolkit`,
`description` < 1024 chars) already satisfies Cline's skill-discovery
requirements.

Cline (confirmed on CLI 3.0.61 with the `cline-pass/glm-5.2` model) auto-injects
the repository-root `AGENTS.md` into the workspace context at session start, so
the shared operating document reaches every model routed through ClinePass
(DeepSeek, GLM, Kimi, Qwen, …) without a per-model entry file. Per-model
`DEEPSEEK.md` / `KIMI.md` / `GLM.md` / `QWEN.md` files are deliberately not
created — those are model providers, not harnesses; the harness (Cline) is the
layer that owns project-context files.
