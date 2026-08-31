# Antigravity CLI adapter

Antigravity plugins are a `plugin.json` marker file plus optional sibling
directories (`skills/`, `agents/`, `rules/`), per
`antigravity.google/docs/cli/plugins/`. This manifest includes `name`,
`version`, `description`, and `$schema`.
**Manually verified against Antigravity's `agy` CLI 1.1.13** (`agy
--version`): validate, install, and discovery all work — see "Verification
status" below.

## Install

1. Symlink this repo's `skills/adr-toolkit/` package under this adapter's
   directory:

   ```bash
   mkdir -p adapters/antigravity/skills
   ln -s "$(pwd)/skills/adr-toolkit" adapters/antigravity/skills/adr-toolkit
   ```

2. Install with Antigravity's own plugin CLI:

   ```bash
   agy plugin install "$(pwd)/adapters/antigravity"
   ```

3. Confirm Antigravity lists `adr-toolkit`:

   ```bash
   agy plugin list
   ```

4. Either way, run
   `python skills/adr-toolkit/scripts/adr.py preflight --json` from your
   target repository to confirm the script layer works standalone.

The symlink is created at install time, not committed to this repo —
committing a real symlink breaks on Windows checkouts that don't have
`core.symlinks` enabled, which this project's CI can't assume.

## Verification status

Manually verified against Antigravity's `agy` CLI 1.1.13 (`agy --version`)
in an isolated `HOME=$(mktemp -d)` so no state was written to the real
`~/.gemini` (Antigravity's plugin CLI stores state under `.gemini/config/`
in the active home directory).

```
$ agy plugin validate "$(pwd)/adapters/antigravity"
  [ok]    <repo-root>/adapters/antigravity
          [check] skills      : 1 processed
          - agents      : skipped (not found)
          - commands    : skipped (not found)
          - mcpServers  : skipped (not found)
          - hooks       : skipped (not found)

$ agy plugin install "$(pwd)/adapters/antigravity"
  [ok]    adr-toolkit
          [check] skills      : 1 processed

$ agy plugin list
{
  "imports": [
    {
      "name": "adr-toolkit",
      "source": "antigravity",
      "importedAt": "2026-08-31T06:11:34Z",
      "components": ["skills"]
    }
  ]
}
```

The installed snapshot lands under `<HOME>/.gemini/config/plugins/adr-toolkit/`
and carries the whole `skills/adr-toolkit/` package. The script layer was
run directly out of it against a scratch git repository, producing correct
`"ok": true` output for `preflight`, `init --dir docs/decisions`, and
`validate --dir docs/decisions` — matching the Codex and Gemini CLI
adapters' verified depth.
