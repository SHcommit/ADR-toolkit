"""Proves INDEX's generated README cannot be split into a second,
attacker-controlled link via an ADR title (docs/adr-toolkit-audit-report.md,
Top-3 #2)."""
from pathlib import Path
from types import SimpleNamespace

from scripts.commands import index


_MALICIOUS_ADR = (
    "---\n"
    "id: ADR-0001\n"
    "title: foo](http://evil.example)[bar\n"
    "status: accepted\n"
    "date: 2026-01-01\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths: []\n"
    "tags: []\n"
    "retrospective: false\n"
    "---\n\n"
    "Body.\n"
)


def test_index_readme_cannot_be_split_into_a_second_link(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-test.md").write_text(_MALICIOUS_ADR, encoding="utf-8")

    result = index.run(SimpleNamespace(dir=str(adr_dir), root=str(tmp_path), locale=None))
    assert result["ok"] is True

    readme = (adr_dir / "README.md").read_text(encoding="utf-8")
    # An unescaped "](...)[ " sequence is what a Markdown renderer reads as
    # "close this link, open a second one" -- it must not appear.
    assert "](http://evil.example)[" not in readme
    assert "foo\\]\\(http://evil.example\\)\\[bar" in readme
