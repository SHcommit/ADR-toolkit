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


def test_cline_entry_file_is_thin_pointer_to_agents_md():
    # Cline joins Codex/Claude/Gemini as a harness with a thin entry file that
    # delegates to AGENTS.md. Per-model entry files (DEEPSEEK/GLM/KIMI/QWEN) are
    # intentionally not created — those are models routed through a harness,
    # not harnesses themselves.
    cline_entry = REPO_ROOT / "CLINE.md"
    text = cline_entry.read_text(encoding="utf-8")
    assert "AGENTS.md" in text
    assert "Follow the shared project rules" in text
    # Harness entry files must stay thin — no duplication of AGENTS.md rules.
    assert "Git Flow" not in text
    assert "Release tags" not in text


def test_agents_md_lists_cline_among_harnesses():
    text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    # Cline must be listed both in the harness enumeration and the entry-file
    # paragraph, alongside Codex/Claude/Gemini.
    assert "Cline" in text
    assert "CLINE.md" in text
    # And the per-model-file non-creation policy must be stated.
    assert "model/API providers" in text


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
