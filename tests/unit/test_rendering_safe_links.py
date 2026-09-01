"""Tests for Markdown link-text escaping (docs/adr-toolkit-audit-report.md,
Top-3 #2)."""
from scripts.core.rendering import safe_md_link_text


def test_escapes_characters_that_break_out_of_link_text():
    result = safe_md_link_text("foo](http://evil.example)[bar")
    assert result == "foo\\]\\(http://evil.example\\)\\[bar"


def test_collapses_embedded_newlines_to_spaces():
    result = safe_md_link_text("line one\nline two")
    assert result == "line one line two"


def test_leaves_ordinary_titles_unchanged():
    result = safe_md_link_text("Adopt PostgreSQL for primary storage")
    assert result == "Adopt PostgreSQL for primary storage"
