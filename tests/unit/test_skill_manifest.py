from pathlib import Path

from scripts.core import frontmatter as fm

SKILL_MD = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit" / "SKILL.md"
REFERENCES = SKILL_MD.parent / "references"


def test_skill_md_frontmatter_has_required_fields():
    data, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    assert data["name"] == "adr-toolkit"
    assert data["user-invocable"] is True
    assert "description" in data
    assert "version" in data


def test_skill_md_documents_the_workflow_stages():
    _, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    for stage in ["PREFLIGHT", "DISCOVER", "CLASSIFY", "ASK-IF-NEEDED", "PLAN", "CONFIRM", "MUTATE", "VALIDATE", "REPORT"]:
        assert stage in body


def test_skill_md_separates_init_and_discover_operations():
    _, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    assert "## INIT" in body
    assert "## DISCOVER" in body
    assert "## What belongs in an ADR" in body


def test_skill_md_requires_evidence_inference_separation_for_retrospective_adrs():
    _, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    assert "Confirmed Evidence" in body
    assert "Inferred Rationale" in body
    assert "## Unknown" in body


def test_reference_files_exist():
    assert (REFERENCES / "lifecycle.md").is_file()
    assert (REFERENCES / "madr-guide.md").is_file()


def test_skill_md_documents_check():
    _, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    assert "## CHECK" in body
    assert "adr.py check" in body
    assert "Verified violation" in body
    assert "CHECK is not yet implemented" not in body
