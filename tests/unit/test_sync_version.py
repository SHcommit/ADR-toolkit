import importlib.util
import json
from pathlib import Path

# scripts/sync_version.py lives in a repo-root `scripts/` package. A separate,
# unrelated `scripts/` package also exists under skills/adr-toolkit/, and
# tests/conftest.py puts that one on sys.path (so skill-internal tests can do
# `from scripts.core import frontmatter`). Because skills/adr-toolkit/scripts
# has an __init__.py, it is a *regular* package and Python's import system
# binds the top-level name "scripts" to it for the whole test session as soon
# as anything imports it — a plain `from scripts.sync_version import sync`
# here would resolve against that other package and fail with
# ModuleNotFoundError. Load this module directly by file path instead, so it
# never touches the ambient (and already-claimed) "scripts" name.
_SYNC_VERSION_PATH = Path(__file__).resolve().parents[2] / "scripts" / "sync_version.py"
_spec = importlib.util.spec_from_file_location("_repo_root_sync_version", _SYNC_VERSION_PATH)
_sync_version = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sync_version)

sync = _sync_version.sync
sync_skill_md = _sync_version.sync_skill_md

MANIFEST_SPECS = [("plugin.json", ["version"]), ("nested.json", ["meta", "version"])]


def _write(tmp_path, name, data):
    path = tmp_path / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_sync_writes_matching_version_into_every_manifest(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    plugin = _write(tmp_path, "plugin.json", {"name": "x", "version": "0.0.0"})
    nested = _write(tmp_path, "nested.json", {"meta": {"version": "0.0.0"}})

    changed = sync(version_file, [(plugin, ["version"]), (nested, ["meta", "version"])], check_only=False)

    assert json.loads(plugin.read_text())["version"] == "1.2.3"
    assert json.loads(nested.read_text())["meta"]["version"] == "1.2.3"
    assert set(changed) == {plugin, nested}


def test_sync_is_idempotent_when_already_synced(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    plugin = _write(tmp_path, "plugin.json", {"name": "x", "version": "1.2.3"})

    changed = sync(version_file, [(plugin, ["version"])], check_only=False)

    assert changed == []


def test_check_only_mode_reports_drift_without_writing(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    plugin = _write(tmp_path, "plugin.json", {"name": "x", "version": "0.0.0"})

    changed = sync(version_file, [(plugin, ["version"])], check_only=True)

    assert changed == [plugin]
    assert json.loads(plugin.read_text())["version"] == "0.0.0"


def test_manifest_missing_a_version_key_is_skipped_not_added(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    frontmatter_like = _write(tmp_path, "nokey.json", {"name": "x"})

    changed = sync(version_file, [(frontmatter_like, ["version"])], check_only=False)

    assert changed == []
    assert "version" not in json.loads(frontmatter_like.read_text())


def test_sync_skill_md_updates_frontmatter_version_line(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text(
        "---\nname: adr-toolkit\nversion: 0.0.0\n---\n\n# ADR Toolkit\n", encoding="utf-8",
    )

    changed = sync_skill_md(version_file, skill_md, check_only=False)

    assert changed is True
    updated = skill_md.read_text(encoding="utf-8")
    assert "version: 1.2.3" in updated
    assert "name: adr-toolkit" in updated  # untouched fields survive unchanged


def test_sync_skill_md_check_only_does_not_write(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\nversion: 0.0.0\n---\n\nBody\n", encoding="utf-8")

    changed = sync_skill_md(version_file, skill_md, check_only=True)

    assert changed is True
    assert "version: 0.0.0" in skill_md.read_text(encoding="utf-8")


def test_sync_skill_md_idempotent_when_already_synced(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")
    skill_md = tmp_path / "SKILL.md"
    skill_md.write_text("---\nversion: 1.2.3\n---\n\nBody\n", encoding="utf-8")

    changed = sync_skill_md(version_file, skill_md, check_only=False)

    assert changed is False
