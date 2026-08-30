from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit"


def test_skill_root_layout_exists():
    assert (SKILL_ROOT / "VERSION").is_file()
    assert (SKILL_ROOT / "scripts" / "__init__.py").is_file()
    assert (SKILL_ROOT / "scripts" / "core" / "__init__.py").is_file()
    assert (SKILL_ROOT / "scripts" / "commands" / "__init__.py").is_file()
    assert (SKILL_ROOT / "scripts" / "evidence" / "__init__.py").is_file()
    assert (SKILL_ROOT / "templates").is_dir()
    assert (SKILL_ROOT / "references").is_dir()
    assert (SKILL_ROOT / "schemas").is_dir()


def test_version_file_has_semver():
    version = (SKILL_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    parts = version.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)


def test_scripts_importable_via_conftest_path():
    import scripts  # noqa: F401 — only importable if conftest.py set sys.path correctly
