# Gemini CLI adapter

Gemini CLI extensions declare themselves via a root `gemini-extension.json`
(see `geminicli.com/docs/extensions/reference/`), expecting a sibling
`skills/` directory holding `SKILL.md` files. **Manually verified against
Gemini CLI 0.46.0** (`gemini --version`): install and discovery both work
exactly as the spec describes — see "Verification status" below.

## Install

1. Symlink this repo's `skills/adr-toolkit/` package under this adapter's
   directory:

   ```bash
   mkdir -p adapters/gemini-cli/skills
   ln -s "$(pwd)/skills/adr-toolkit" adapters/gemini-cli/skills/adr-toolkit
   ```

2. Install the extension with Gemini CLI's own extension-install command:

   ```bash
   gemini extensions install "$(pwd)/adapters/gemini-cli"
   ```

   Gemini CLI will prompt twice — once to trust the folder, once to confirm
   the agent skill it found — before installing. Confirm the exact syntax
   against `gemini extensions --help`, since command surfaces move faster
   than this file.

3. Confirm Gemini CLI lists `adr-toolkit` as an installed extension:

   ```bash
   gemini extensions list
   ```

4. Either way, run
   `python skills/adr-toolkit/scripts/adr.py preflight --json` from your
   target repository to confirm the script layer works standalone — this
   is the verified working path regardless of extension-discovery status.

The symlink is created at install time, not committed to this repo —
committing a real symlink breaks on Windows checkouts that don't have
`core.symlinks` enabled, which this project's CI can't assume.

## Verification status

Manually verified against Gemini CLI 0.46.0 (`gemini --version`) in a
scratch git repository with `skills/adr-toolkit` symlinked in per step 1
above. Unlike the Codex CLI adapter (whose plugin CLI does not yet
auto-discover a bare single-plugin manifest), Gemini CLI's extension
system worked cleanly end to end:

- `gemini extensions validate <path>` reported
  `Extension <path> has been successfully validated.`
- `gemini extensions install <path>` prompted to trust the folder, then
  detected the `adr-toolkit` agent skill from
  `skills/adr-toolkit/SKILL.md` and installed it after confirmation:
  `Extension "adr-toolkit" installed successfully and enabled.`
- `gemini extensions list` afterward showed:

  ```
  ✓ adr-toolkit (0.1.0)
   Path: ~/.gemini/extensions/adr-toolkit
   Source: <scratch-dir> (Type: local)
   Enabled (User): true
   Enabled (Workspace): true
   Agent skills:
    adr-toolkit: Initialize, record, and check Architecture Decision
    Records by inspecting the repository and existing decisions before
    asking questions.
  ```

So both install-time discovery (step 3's checkpoint) and the script-layer
fallback (step 4) are confirmed working. The script layer was also run
directly through the symlink and produced correct `"ok": true` output for
`preflight`, `init --dir docs/decisions`, and `validate --dir
docs/decisions`, independent of extension installation.
