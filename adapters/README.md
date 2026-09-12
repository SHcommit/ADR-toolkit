# Harness Adapters

This directory contains harness-specific adapters and integration documentation for connecting `adr-toolkit` to various AI coding assistants and CLI harnesses.

---

## Supported Harnesses

| Harness Adapter | Directory | Type | Key Files |
| :--- | :--- | :--- | :--- |
| **Claude Code** | `adapters/claude/` | Manifest-based | `.claude-plugin/plugin.json`, `marketplace.json` |
| **Codex CLI** | `adapters/codex/` | Manifest-based | `adapters/codex/marketplace.json` |
| **Gemini CLI** | `adapters/gemini-cli/` | Manifest-based | `adapters/gemini-cli/gemini-extension.json` |
| **Antigravity CLI** | `adapters/antigravity/` | Manifest-based | `adapters/antigravity/plugin.json` |
| **Cline CLI / ClinePass** | `adapters/cline/` | Documentation (SKILL.md standard) | `adapters/cline/README.md` |
| **Generic Agent** | `adapters/generic/` | Open Agent Skills Standard | `adapters/generic/README.md` |

---

## Tutorial: Adding a New Harness Adapter

Follow these step-by-step instructions to create an adapter for a new AI coding assistant or CLI harness.

### Step 1: Create the Adapter Directory
Create a dedicated subdirectory under `adapters/`:
```bash
mkdir -p adapters/<harness-name>
```

### Step 2: Determine Adapter Type

#### Type A: Manifest-Based Adapter
If the harness supports native CLI plugin or extension registries via JSON manifests:
1. Create the required JSON manifest in `adapters/<harness-name>/` or root configuration directory.
2. Ensure the manifest references `skills/adr-toolkit` as its skill target.
3. Write a clear `adapters/<harness-name>/README.md` explaining installation and CLI discovery commands.

#### Type B: Open Agent Skills Standard (README-Only)
If the harness natively supports the open `SKILL.md` standard (like Cline or Generic Agents):
1. No separate manifest JSON is needed.
2. Create `adapters/<harness-name>/README.md` detailing the standard installation command (e.g., skill add commands or symlinks).

### Step 3: Register in Version Sync Tooling (If Applicable)
If your adapter contains a JSON manifest with a hardcoded version string:
- Register the manifest file path and JSON key pattern in `scripts/sync_version.py`.
- Add a corresponding regression test in `tests/unit/test_<harness_name>_adapter.py`.

### Step 4: Verification and CI Integration
1. Run `python scripts/sync_version.py --check` to verify no version drift.
2. Add end-to-end integration test steps to `.github/workflows/test.yml` under the `harness-parity` job if automated CLI testing is supported.
