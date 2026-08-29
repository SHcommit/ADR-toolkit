from pathlib import Path

REFERENCE = (
    Path(__file__).resolve().parent.parent.parent
    / "skills" / "adr-toolkit" / "references" / "conflict-rules.md"
)


def test_reference_documents_all_six_rule_kinds():
    text = REFERENCE.read_text(encoding="utf-8")
    for kind in [
        "forbidden_import", "required_path", "forbidden_path",
        "dependency_forbidden", "file_must_exist", "test_must_exist",
    ]:
        assert kind in text


def test_reference_documents_the_four_classifications():
    text = REFERENCE.read_text(encoding="utf-8")
    for label in ["Related", "Review required", "Verified violation", "No applicable constraint"]:
        assert label in text


def test_reference_documents_the_five_resolutions():
    text = REFERENCE.read_text(encoding="utf-8")
    for resolution in ["fix_code", "supersede_adr", "adjust_scope", "register_exception", "false_positive"]:
        assert resolution in text
