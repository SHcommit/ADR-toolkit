import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLUGIN_DIR = REPO_ROOT / ".claude-plugin"


def test_plugin_manifest_has_required_keys_and_no_skills_key():
    manifest = json.loads((PLUGIN_DIR / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "adr-toolkit"
    assert "version" in manifest
    assert "skills" not in manifest, (
        "Claude Code auto-discovers <plugin-root>/skills/; plugin.json must not list them"
    )


def test_skill_is_discoverable_at_the_auto_discovery_convention_path():
    # The whole repo is the plugin, so Claude Code's auto-discovery convention
    # (<plugin-root>/skills/<name>/SKILL.md) is relative to the repo root.
    skill_md = REPO_ROOT / "skills" / "adr-toolkit" / "SKILL.md"
    assert skill_md.is_file()


def test_marketplace_manifest_lists_the_plugin():
    marketplace = json.loads((PLUGIN_DIR / "marketplace.json").read_text(encoding="utf-8"))
    names = [p["name"] for p in marketplace["plugins"]]
    assert "adr-toolkit" in names
