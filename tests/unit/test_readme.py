from pathlib import Path

README = Path(__file__).resolve().parents[2] / "README.md"


def test_readme_documents_repository_locale_configuration():
    text = README.read_text(encoding="utf-8")
    assert ".adr-toolkit.json" in text
    for locale in ["en", "ko", "ja", "zh", "fr", "es", "de", "pt-BR"]:
        assert f"`{locale}`" in text
    assert "init --locale ko" in text
    assert "create --interactive" in text
    assert "create --locale ja" in text
    assert "index --locale fr" in text


def test_readme_documents_non_ascii_titles_and_semantic_slugs():
    text = README.read_text(encoding="utf-8")
    assert "결제 시스템 분리" in text
    assert "--slug separate-payment-system" in text
    assert "0001-decision.md" in text


def test_readme_scopes_check_confidence():
    text = README.read_text(encoding="utf-8")
    assert "CHECK does not certify the entire architecture" in text
    for label in ["VERIFIED", "VIOLATED", "UNVERIFIABLE", "NOT_APPLICABLE"]:
        assert label in text
