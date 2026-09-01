import importlib.util
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST = REPO_ROOT / "adapters" / "antigravity" / "plugin.json"

NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")

_ADAPTER_SDK_PATH = REPO_ROOT / "scripts" / "adapter_sdk.py"
_spec = importlib.util.spec_from_file_location("_repo_root_adapter_sdk", _ADAPTER_SDK_PATH)
adapter_sdk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adapter_sdk)


def test_manifest_is_valid_json_with_required_fields():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["name"] == "adr-toolkit"


def test_manifest_name_matches_antigravity_naming_rule():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert NAME_RE.match(data["name"]), "name must be alphanumeric, hyphens, or underscores only"


def test_manifest_schema_field_points_at_antigravity_schema():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["$schema"] == "https://antigravity.google/schemas/v1/plugin.json"


def test_manifest_passes_the_shared_adapter_validator():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert adapter_sdk.validate_adapter_manifest(data) == []
