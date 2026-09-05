# Cline CLI adapter

Cline CLI installs skills through the **open Agent Skills** standard — the same
`SKILL.md` + `skills/` convention this toolkit already ships — rather than a
harness-specific manifest file like the Codex, Gemini, and Antigravity adapters
use. There is no `plugin.json`/`gemini-extension.json` equivalent for Cline
skills, so this adapter is **README-only** (like `adapters/generic/`): it
documents how to point Cline at the existing `skills/adr-toolkit/` package.
**Manually verified against Cline CLI 3.0.61** (`cline --version`): discovery,
install, and the installed script layer all work — see "Verification status"
below.

Cline CLI exposes a `skill` subcommand that forwards to the open skills CLI
(`npx skills`), and it discovers skills from the standard agent locations
(`~/.agents/skills/` globally, `.cline/skills/` per project). Because
`skills/adr-toolkit/SKILL.md` already carries the two fields Cline requires —
`name` matching its directory and `description` (under 1024 characters) — the
package installs as-is with no wrapper.

## Install

### From the published repository (recommended)

The repository is public, so Cline installs the skill straight from GitHub:

```bash
cline skill add SHcommit/ADR-toolkit --global
```

Add `-y`/`--yes` to skip the confirmation prompt. Drop `--global` to install
project-level (into the current project's `.cline/skills/`) instead of globally.

### From a local clone

A local checkout works the same way:

```bash
cline skill add "$(pwd)/skills/adr-toolkit" --global
```

or symlink the package into Cline's skill directory yourself:

```bash
# project-level
mkdir -p .cline/skills
ln -s "$(pwd)/skills/adr-toolkit" .cline/skills/adr-toolkit

# global
mkdir -p ~/.agents/skills
ln -s "$(pwd)/skills/adr-toolkit" ~/.agents/skills/adr-toolkit
```

The symlink is created at install time, not committed to any repo — committing a
real symlink breaks on Windows checkouts that don't have `core.symlinks` enabled,
which this project's CI can't assume.

### Confirm

```bash
cline skill list
```

should list `adr-toolkit`.

### Script-layer fallback

Either way, run
`python skills/adr-toolkit/scripts/adr.py preflight --json` from your target
repository to confirm the script layer works standalone — this is the verified
working path regardless of skill-discovery status.

## Why there's no manifest here

Cline's "plugin" mechanism (`cline plugin install`, driven by a `package.json`
`cline` field) is for **TypeScript `AgentPlugin` modules** that register tools
and lifecycle hooks — a different extension point from a skill. ADR Toolkit is a
Python skill, so a TS plugin wrapper would be a rewrite with no benefit. The
always-on-hook use case (auto-running `check` on session start) is deliberately
out of scope — see `project-roadmap.md`'s "Harness parity" note.

## Verification status

Manually verified against Cline CLI 3.0.61 (`cline --version`) in an isolated
`HOME=$(mktemp -d)` so no state was written to the real `~/.cline`/`~/.agents`.

```
$ cline skill add SHcommit/ADR-toolkit --list
...
◇  Found 1 skill
│    adr-toolkit
│      Initialize, record, and check Architecture Decision Records by inspecting the repository and existing decisions before asking questions.

$ cline skill add SHcommit/ADR-toolkit --yes --global
...
◇  Installed 1 skill
│  ✓ adr-toolkit (copied)
│    → ~/.agents/skills/adr-toolkit
```

The installed snapshot lands under `~/.agents/skills/adr-toolkit/` and carries
the whole `skills/adr-toolkit/` package. The script layer was run directly out of
it against a scratch git repository, producing correct `"ok": true` output for
`preflight`, `init --dir docs/decisions`, and `validate --dir docs/decisions` —
matching the Codex, Gemini CLI, and Antigravity adapters' verified depth.

Two details worth knowing:

- **The install location is `~/.agents/skills/`, not `~/.cline/...`.** The
  skills CLI reports `~/.agents/skills/adr-toolkit` as the install path (the open
  Agent Skills global directory Cline reads), even though Cline's CLI reference
  mentions a `~/.cline/data/settings/skills/` global directory. Trust
  `cline skill list` for where a given Cline version actually looks.
- **A project's own `skills/` directory is auto-detected.** Running
  `cline skill list` inside this repository reports `adr-toolkit` from
  `./skills/adr-toolkit` as a project skill, so a checkout of this repo is already
  a working Cline project skill with no install step.
