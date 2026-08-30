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
    assert "does not certify the entire architecture" in body
    for label in ["VERIFIED", "VIOLATED", "UNVERIFIABLE", "NOT_APPLICABLE"]:
        assert label in body


def test_record_points_at_the_conflict_rules_reference_for_constraints_blocks():
    _, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    assert "constraints:" in body
    assert "references/conflict-rules.md" in body


def test_skill_md_documents_locale_detection():
    _, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    assert "--locale" in body
    for locale in ["en", "ko", "ja", "zh", "fr", "es", "de", "pt-BR"]:
        assert locale in body
    assert "explicit user request" in body
    assert "request language" in body
    assert "repository default" in body


def test_skill_md_requires_semantic_slug_confirmation():
    _, body = fm.parse(SKILL_MD.read_text(encoding="utf-8"))
    assert "semantic ASCII slug" in body
    assert "--slug" in body
    assert "show" in body and "CONFIRM" in body
