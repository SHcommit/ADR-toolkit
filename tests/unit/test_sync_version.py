import importlib.util
import json
from pathlib import Path

import pytest

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


read_version = _sync_version.read_version
replace_version_line = _sync_version.replace_version_line
require_known_paths = _sync_version.require_known_paths
REAL_MANIFEST_SPECS = _sync_version.MANIFEST_SPECS
REAL_SKILL_MD_PATH = _sync_version.SKILL_MD_PATH
REAL_VERSION_FILE = _sync_version.VERSION_FILE


# --- VERSION content validation (finding 6) ---------------------------------

def test_empty_version_file_raises_instead_of_writing_an_empty_version(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("   \n", encoding="utf-8")
    plugin = _write(tmp_path, "plugin.json", {"name": "x", "version": "0.0.0"})

    with pytest.raises(SystemExit):
        sync(version_file, [(plugin, ["version"])], check_only=False)

    assert json.loads(plugin.read_text())["version"] == "0.0.0"


def test_version_with_an_internal_newline_is_rejected(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2\n.3\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        read_version(version_file)


def test_version_with_regex_template_characters_is_rejected(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text(r"1.2.3-\g<0>" + "\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        read_version(version_file)


def test_prerelease_version_is_accepted(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3-rc.1\n", encoding="utf-8")

    assert read_version(version_file) == "1.2.3-rc.1"


def test_version_line_replacement_is_literal_not_a_regex_template():
    """re.sub would expand \\g<0>/\\1 in a template string; the callable must not."""
    text = "---\nversion: 0.0.0\n---\n\nBody\n"

    result = replace_version_line(text, r"1.2.3-\g<0>")

    assert r"version: 1.2.3-\g<0>" in result
    assert "version: 0.0.0" not in result


def test_version_line_replacement_handles_backreference_syntax():
    text = "---\nversion: 0.0.0\n---\n"

    assert r"version: \1" in replace_version_line(text, r"\1")


# --- The real, module-level manifest constants (finding 7) ------------------

def test_every_real_manifest_spec_exists_with_its_declared_key():
    for path, key_path in REAL_MANIFEST_SPECS:
        assert path.is_file(), f"tracked manifest is missing: {path}"
        target = json.loads(path.read_text(encoding="utf-8"))
        for key in key_path:
            assert isinstance(target, dict) and key in target, (
                f"{path} has no {'.'.join(key_path)} key"
            )
            target = target[key]
        assert isinstance(target, str) and target


def test_real_version_file_and_skill_md_exist_and_agree():
    assert REAL_VERSION_FILE.is_file()
    assert REAL_SKILL_MD_PATH.is_file()
    version = read_version(REAL_VERSION_FILE)
    assert f"version: {version}" in REAL_SKILL_MD_PATH.read_text(encoding="utf-8")


def test_require_known_paths_passes_against_the_real_repo():
    require_known_paths()  # must not raise


def test_require_known_paths_raises_when_a_tracked_manifest_disappears(monkeypatch):
    missing = REAL_MANIFEST_SPECS[0][0].parent / "definitely-not-here.json"
    monkeypatch.setattr(_sync_version, "MANIFEST_SPECS", [(missing, ["version"])])

    with pytest.raises(SystemExit) as excinfo:
        require_known_paths()

    assert "definitely-not-here.json" in str(excinfo.value)


def test_sync_still_tolerates_a_missing_fixture_path_for_testability(tmp_path):
    version_file = tmp_path / "VERSION"
    version_file.write_text("1.2.3\n", encoding="utf-8")

    assert sync(version_file, [(tmp_path / "absent.json", ["version"])], check_only=True) == []
