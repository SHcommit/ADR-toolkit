import importlib.util
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST = REPO_ROOT / "adapters" / "gemini-cli" / "gemini-extension.json"

_ADAPTER_SDK_PATH = REPO_ROOT / "scripts" / "adapter_sdk.py"
_spec = importlib.util.spec_from_file_location("_repo_root_adapter_sdk", _ADAPTER_SDK_PATH)
adapter_sdk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adapter_sdk)


def test_manifest_is_valid_json_with_required_fields():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["name"] == "adr-toolkit"


def test_manifest_name_uses_dashes_not_underscores_or_spaces():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert " " not in data["name"]
    assert "_" not in data["name"]


def test_manifest_passes_the_shared_adapter_validator():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert adapter_sdk.validate_adapter_manifest(data) == []
