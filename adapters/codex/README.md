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

1. Symlink this repo's `skills/adr-toolkit/` package under this adapter's
   directory, as a sibling of `.codex-plugin/` (design spec §17.2):

   ```bash
   mkdir -p adapters/codex/skills
   ln -s "$(pwd)/skills/adr-toolkit" adapters/codex/skills/adr-toolkit
   ```

2. Register this repository as a Codex marketplace and install the plugin:

   ```bash
   codex plugin marketplace add "$(pwd)"
   codex plugin add adr-toolkit@adr-toolkit-marketplace
   ```

   The marketplace name (`adr-toolkit-marketplace`) is the `"name"` field of
   `.claude-plugin/marketplace.json`; `codex plugin marketplace add` prints it
   on success, and `codex plugin marketplace list` shows it later.

3. Confirm Codex lists `adr-toolkit` as installed and enabled:

   ```bash
   codex plugin list
   ```

4. Optionally run
   `python skills/adr-toolkit/scripts/adr.py preflight --json` from your
   target repository to confirm the script layer works standalone.

The symlink is created at install time, not committed to this repo —
committing a real symlink breaks on Windows checkouts that don't have
`core.symlinks` enabled, which this project's CI can't assume. `.gitignore`
already ignores `adapters/codex/skills/adr-toolkit` so a `git add -A` after
step 1 cannot commit it by accident.

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
