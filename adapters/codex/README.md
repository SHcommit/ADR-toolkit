# Codex CLI adapter

Follows the cross-vendor Agent Plugins 1.0.0 standard
(`github.com/agentplugins/agent-plugins-spec`), which Codex CLI adopted
2026-08-07. Per the standard, this manifest needs only `name` — no
`"skills"` key, since Agent Plugins is specified to auto-discover a
sibling `skills/` directory. **Manually verified against Codex CLI
0.151.0** (`codex --version`): install and discovery both work — see
"Verification status" below.

## Install

Codex CLI's plugin CLI is **marketplace-based**: `codex plugin add` installs
a plugin from a marketplace root that Codex has already been told about, not
from a bare plugin directory. This repository is already a valid marketplace
root, because its `.claude-plugin/marketplace.json` is a manifest format
Codex CLI reads, so no extra manifest is needed.

1. Register this repository as a Codex marketplace and install the plugin:

   ```bash
   codex plugin marketplace add "$(pwd)"
   codex plugin add adr-toolkit@adr-toolkit-marketplace
   ```

   The marketplace name (`adr-toolkit-marketplace`) is the `"name"` field of
   `.claude-plugin/marketplace.json`; `codex plugin marketplace add` prints it
   on success, and `codex plugin marketplace list` shows it later.

2. Confirm Codex lists `adr-toolkit` as installed and enabled:

   ```bash
   codex plugin list
   ```

3. Optionally run
   `python skills/adr-toolkit/scripts/adr.py preflight --json` from your
   target repository to confirm the script layer works standalone.

No symlink step is required. Registering the repository **root** as the
marketplace means Codex reads `.claude-plugin/plugin.json` as the plugin
manifest, and Agent Plugins' sibling-`skills/`-directory discovery finds the
real `skills/adr-toolkit/` package next to it directly — verified below by
installing with no `adapters/codex/skills/` symlink present at all.

## Why `.codex-plugin/plugin.json` and an adapter-local symlink exist here too

Design spec §17.2 originally planned every harness adapter as a
**self-contained** plugin directory: `adapters/codex/.codex-plugin/plugin.json`
as that harness's own manifest, with `adapters/codex/skills/adr-toolkit`
symlinked in as its required sibling `skills/` directory
(`ln -s ../../../skills/adr-toolkit adapters/codex/skills/adr-toolkit`), so
each adapter would work if pointed at directly.

That plan does not hold for Codex specifically: `codex plugin marketplace add`
rejects a bare single-plugin directory —

```
$ codex plugin marketplace add "$(pwd)/adapters/codex"
Error: invalid marketplace file `<repo-root>/adapters/codex`: marketplace root does not contain a supported manifest
```

— because only the repository root carries a marketplace manifest
(`.claude-plugin/marketplace.json`). So `adapters/codex/.codex-plugin/plugin.json`
and its sibling symlink are never read by the verified install path above;
they exist only for structural consistency with the Gemini and Antigravity
adapters' self-contained layout, and in case a future Codex version accepts a
bare plugin directory as a marketplace root. If you want that manifest to
resolve correctly on its own regardless, create the symlink manually:

```bash
mkdir -p adapters/codex/skills
ln -s "$(pwd)/skills/adr-toolkit" adapters/codex/skills/adr-toolkit
```

This is not committed to the repo — committing a real symlink breaks on
Windows checkouts that don't have `core.symlinks` enabled, which this
project's CI can't assume. `.gitignore` already ignores
`adapters/codex/skills/adr-toolkit` so a `git add -A` cannot commit it by
accident.

## Verification status

Manually verified against Codex CLI 0.151.0 (`codex --version`), run
throughout with an isolated `CODEX_HOME=$(mktemp -d)` so no state was
written to the real `~/.codex`.

```
$ codex plugin marketplace add "$(pwd)"
Added marketplace `adr-toolkit-marketplace` from <repo-root>.
Installed marketplace root: <repo-root>

$ codex plugin add adr-toolkit@adr-toolkit-marketplace --json
{
  "pluginId": "adr-toolkit@adr-toolkit-marketplace",
  "name": "adr-toolkit",
  "marketplaceName": "adr-toolkit-marketplace",
  "version": "0.1.0",
  "installedPath": "<CODEX_HOME>/plugins/cache/adr-toolkit-marketplace/adr-toolkit/0.1.0",
  "authPolicy": "ON_INSTALL"
}

$ codex plugin list
Marketplace `adr-toolkit-marketplace`
<repo-root>/.claude-plugin/marketplace.json

PLUGIN                               STATUS              VERSION  PATH
adr-toolkit@adr-toolkit-marketplace  installed, enabled  0.1.0    <repo-root>
```

The installed snapshot under `<CODEX_HOME>/plugins/cache/` carries the
whole `skills/adr-toolkit/` package, and the script layer was run directly
out of it against a scratch git repository, producing correct `"ok": true`
output for `preflight`, `init --dir docs/decisions`, and
`validate --dir docs/decisions`.

Re-verified with **no `adapters/codex/skills/` symlink present at all**: the
same three commands above still succeed and `preflight --json` still returns
`"ok": true` from the installed snapshot, confirming the symlink step this
README previously listed as install step 1 played no part in the working
flow.

Two details worth knowing:

- **A marketplace root, not a plugin directory, is what you register.**
  Pointing `codex plugin marketplace add` at a bare single-plugin directory
  (this adapter's own `adapters/codex/`, or its `.codex-plugin/`) fails with
  `marketplace root does not contain a supported manifest`. That is Codex's
  documented marketplace model, not a defect; the repo root is the correct
  thing to register, and it works.
- **The version Codex reports comes from the plugin manifest it reads.**
  Installing from this repo's root reports `0.1.0`, taken from
  `.claude-plugin/plugin.json`. Installing a marketplace root whose plugin
  manifest is only this adapter's `.codex-plugin/plugin.json` reports
  `1.0.0` instead, because that manifest carries no `version` field and
  Codex substitutes a default. Adding an explicit `version` to
  `.codex-plugin/plugin.json` is tracked as a follow-up.
