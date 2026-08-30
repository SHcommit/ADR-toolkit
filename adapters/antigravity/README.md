# Antigravity CLI adapter

Antigravity plugins are a `plugin.json` marker file plus optional sibling
directories (`skills/`, `agents/`, `rules/`), per
`antigravity.google/docs/cli/plugins/`. This manifest needs only `name`.

## Install

1. Symlink this repo's `skills/adr-toolkit/` package under this adapter's
   directory:

   ```bash
   mkdir -p adapters/antigravity/skills
   ln -s "$(pwd)/skills/adr-toolkit" adapters/antigravity/skills/adr-toolkit
   ```

2. Install per Antigravity's own plugin-install documentation.
3. Confirm Antigravity lists `adr-toolkit`, then run
   `python skills/adr-toolkit/scripts/adr.py preflight --json` from your
   target repository to confirm the script layer works standalone.

**Verification status:** this adapter's manifest and directory layout are
verified against Antigravity's published schema, but — unlike the Codex
and Gemini CLI adapters — no end-to-end install-and-run was performed,
because no `antigravity` CLI binary was available in the development
environment that built this adapter. Treat it as unverified until someone
with the actual CLI confirms it, and update this note when they do.

The symlink is created at install time, not committed to this repo —
committing a real symlink breaks on Windows checkouts that don't have
`core.symlinks` enabled, which this project's CI can't assume.
