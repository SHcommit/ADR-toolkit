import json
from pathlib import Path

MANIFEST = (
    Path(__file__).resolve().parent.parent.parent
    / "adapters" / "codex" / ".codex-plugin" / "plugin.json"
)


def test_manifest_is_valid_json_with_required_fields():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["name"] == "adr-toolkit"


def test_manifest_has_no_extra_undocumented_top_level_keys():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert set(data.keys()) <= {"$schema", "name", "description"}
