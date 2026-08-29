import json
from pathlib import Path

ADAPTER_DIR = Path(__file__).resolve().parent.parent.parent / "adapters" / "claude"


def test_plugin_manifest_has_required_keys():
    manifest = json.loads((ADAPTER_DIR / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "adr-toolkit"
    assert "version" in manifest
    assert manifest["skills"], "plugin.json must list at least one skill path"


def test_plugin_manifest_skill_path_resolves_to_real_skill():
    manifest = json.loads((ADAPTER_DIR / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    skill_path = (ADAPTER_DIR / ".claude-plugin" / manifest["skills"][0]).resolve()
    assert skill_path.is_dir()
    assert (skill_path / "SKILL.md").is_file()


def test_marketplace_manifest_lists_the_plugin():
    marketplace = json.loads((ADAPTER_DIR / "marketplace.json").read_text(encoding="utf-8"))
    names = [p["name"] for p in marketplace["plugins"]]
    assert "adr-toolkit" in names
