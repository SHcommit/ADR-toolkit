"""Tests for the shared adapter-manifest validator
(docs/adr-toolkit-audit-report.md §2.6 6.3)."""
import importlib.util
from pathlib import Path

_ADAPTER_SDK_PATH = Path(__file__).resolve().parents[2] / "scripts" / "adapter_sdk.py"
_spec = importlib.util.spec_from_file_location("_repo_root_adapter_sdk", _ADAPTER_SDK_PATH)
adapter_sdk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(adapter_sdk)


def test_valid_manifest_has_no_errors():
    errors = adapter_sdk.validate_adapter_manifest(
        {"name": "adr-toolkit", "description": "Does the thing."}
    )
    assert errors == []


def test_missing_name_is_reported():
    errors = adapter_sdk.validate_adapter_manifest({"description": "Does the thing."})
    assert any("name" in e for e in errors)


def test_missing_description_is_reported():
    errors = adapter_sdk.validate_adapter_manifest({"name": "adr-toolkit"})
    assert any("description" in e for e in errors)


def test_empty_string_fields_are_rejected():
    errors = adapter_sdk.validate_adapter_manifest({"name": "", "description": "  "})
    assert len(errors) == 2


def test_non_string_fields_are_rejected():
    errors = adapter_sdk.validate_adapter_manifest({"name": 123, "description": None})
    assert len(errors) == 2
