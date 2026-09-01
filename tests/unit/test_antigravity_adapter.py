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


def test_antigravity_adapter_directory_layout_and_symlink_structure(tmp_path):
    # Simulate Antigravity plugin installation layout:
    # adapters/antigravity/plugin.json + skills/adr-toolkit symlink
    repo_root = Path(__file__).resolve().parents[2]
    adapter_dir = tmp_path / "adapters" / "antigravity"
    adapter_dir.mkdir(parents=True)

    manifest_copy = adapter_dir / "plugin.json"
    manifest_copy.write_text(MANIFEST.read_text(encoding="utf-8"), encoding="utf-8")

    skills_dir = adapter_dir / "skills"
    skills_dir.mkdir()
    target_skill = repo_root / "skills" / "adr-toolkit"
    symlink_path = skills_dir / "adr-toolkit"

    try:
        symlink_path.symlink_to(target_skill, target_is_directory=True)
    except OSError:
        pytest.skip("Symlink creation not supported on this platform/user permission")

    assert manifest_copy.is_file()
    assert (symlink_path / "SKILL.md").is_file()
    manifest_data = json.loads(manifest_copy.read_text(encoding="utf-8"))
    assert manifest_data["name"] == "adr-toolkit"


