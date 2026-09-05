from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CLINE_README = REPO_ROOT / "adapters" / "cline" / "README.md"
SKILL_MD = REPO_ROOT / "skills" / "adr-toolkit" / "SKILL.md"


def test_cline_adapter_readme_exists_and_documents_install():
    text = CLINE_README.read_text(encoding="utf-8")
    assert "cline skill add" in text
    assert "skills/adr-toolkit" in text
    assert "SKILL.md" in text


def test_cline_adapter_documents_skill_discovery_locations():
    text = CLINE_README.read_text(encoding="utf-8")
    assert ".cline/skills" in text
    assert "~/.agents/skills" in text


def test_skill_frontmatter_satisfies_cline_requirements():
    # Cline requires `name` to match its directory and `description` (< 1024
    # chars). The canonical package already carries both, so no adapter-local
    # manifest is needed for the Cline adapter.
    text = SKILL_MD.read_text(encoding="utf-8")
    assert "name: adr-toolkit" in text
    assert SKILL_MD.parent.name == "adr-toolkit"
    # Extract the description line from the YAML frontmatter and confirm it is
    # present and under Cline's documented 1024-character limit.
    lines = text.splitlines()
    desc_lines = [
        line[len("description:"):].strip()
        for line in lines
        if line.startswith("description:")
    ]
    assert len(desc_lines) == 1
    assert 0 < len(desc_lines[0]) < 1024
