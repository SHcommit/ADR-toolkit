import json
import re
from pathlib import Path

MANIFEST = (
    Path(__file__).resolve().parent.parent.parent
    / "adapters" / "antigravity" / "plugin.json"
)

NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def test_manifest_is_valid_json_with_required_fields():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["name"] == "adr-toolkit"
    assert "version" in data
    assert "description" in data


def test_manifest_name_matches_antigravity_naming_rule():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert NAME_RE.match(data["name"]), "name must be alphanumeric, hyphens, or underscores only"


def test_manifest_schema_field_points_at_antigravity_schema():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["$schema"] == "https://antigravity.google/schemas/v1/plugin.json"

