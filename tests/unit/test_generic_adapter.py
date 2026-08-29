from pathlib import Path

GENERIC_README = Path(__file__).resolve().parent.parent.parent / "adapters" / "generic" / "README.md"


def test_generic_adapter_readme_exists_and_documents_symlink_install():
    text = GENERIC_README.read_text(encoding="utf-8")
    assert "skills/adr-toolkit" in text
    assert "AGENTS.md" in text
    assert "SKILL.md" in text
