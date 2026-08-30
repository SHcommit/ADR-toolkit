# Codex CLI adapter

Follows the cross-vendor Agent Plugins 1.0.0 standard
(`github.com/agentplugins/agent-plugins-spec`), which Codex CLI adopted
2026-08-07. Per the standard, this manifest needs only `name` — no
`"skills"` key, since Agent Plugins is specified to auto-discover a
sibling `skills/` directory. **As of Codex CLI 0.151.0, Codex's own
`plugin` CLI does not yet implement that auto-discovery** — see
"Verification status" below before relying on steps 2-3.

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
3. If your Codex CLI version's plugin discovery recognizes this layout,
   confirm Codex lists `adr-toolkit` as an available skill. As of Codex
   CLI 0.151.0 this step is known to currently fail (see "Verification
   status" below), so treat it as a check to attempt, not a guaranteed
   checkpoint. Either way, run
   `python skills/adr-toolkit/scripts/adr.py preflight --json` from your
   target repository to confirm the script layer works standalone —
   this is the verified working path.

The symlink is created at install time, not committed to this repo —
committing a real symlink breaks on Windows checkouts that don't have
`core.symlinks` enabled, which this project's CI can't assume.

## Verification status

Manually verified against Codex CLI 0.151.0 (`codex --version`). Codex's
plugin CLI (`codex plugin add|list`, `codex plugin marketplace
add|list|upgrade|remove`) is **marketplace-snapshot-based**: `codex plugin
marketplace add` expects a marketplace-root manifest listing multiple
plugins, not a bare single-plugin `plugin.json` like the one in this
adapter's `.codex-plugin/`. Pointing it at this adapter's plugin directory
(after completing step 1's symlink) currently fails:

```
$ codex plugin marketplace add "$(pwd)/.codex-plugin" --json
Error: invalid marketplace file `.../.codex-plugin`:
marketplace root does not contain a supported manifest
```

In other words, Codex CLI 0.151.0 does not (yet) auto-discover a bare
Agent Plugins 1.0.0 plugin directory the way the cross-vendor spec
describes, so step 3's "Confirm Codex lists `adr-toolkit`" checkpoint will
not currently succeed. The **verified working install path** is steps 1
and 3's fallback: create the symlink, then run
`python .codex-plugin/skills/adr-toolkit/scripts/adr.py preflight --json`
(and `init`/`validate`) directly — this was confirmed to produce correct
`"ok": true` output end-to-end through the symlinked layout, independent
of whether Codex's own plugin discovery recognizes it. This adapter's
manifest and directory layout follow the Agent Plugins 1.0.0 standard as
specified; the gap is in Codex CLI's current implementation of that
standard, not in this adapter.
