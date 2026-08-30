import json
from pathlib import Path

MANIFEST = (
    Path(__file__).resolve().parent.parent.parent
    / "adapters" / "gemini-cli" / "gemini-extension.json"
)


def test_manifest_is_valid_json_with_required_fields():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["name"] == "adr-toolkit"


def test_manifest_name_uses_dashes_not_underscores_or_spaces():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert " " not in data["name"]
    assert "_" not in data["name"]
