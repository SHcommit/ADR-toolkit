# Codex CLI adapter

Follows the cross-vendor Agent Plugins 1.0.0 standard
(`github.com/agentplugins/agent-plugins-spec`), which Codex CLI adopted
2026-08-07. This manifest needs only `name` — no `"skills"` key, since
Agent Plugins auto-discovers a sibling `skills/` directory.

## Install

1. Copy this repo's `skills/adr-toolkit/` package somewhere Codex can
   reach it, then symlink it under this adapter's plugin directory as
   `skills/adr-toolkit` (a sibling of `plugin.json`, inside
   `.codex-plugin/`):

   ```bash
   mkdir -p adapters/codex/.codex-plugin/skills
   ln -s "$(pwd)/skills/adr-toolkit" adapters/codex/.codex-plugin/skills/adr-toolkit
   ```

2. Point Codex at `adapters/codex/.codex-plugin/` per Codex's own plugin
   install documentation (`codex --help` documents the exact
   install/reload subcommand — it may change as the Agent Plugins
   standard matures, since this adapter shipped within days of the
   standard's own release).
3. Confirm Codex lists `adr-toolkit` as an available skill, then run
   `python skills/adr-toolkit/scripts/adr.py preflight --json` from your
   target repository to confirm the script layer works standalone.

The symlink is created at install time, not committed to this repo —
committing a real symlink breaks on Windows checkouts that don't have
`core.symlinks` enabled, which this project's CI can't assume.
