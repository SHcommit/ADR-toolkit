"""Proves search/index don't blow up catastrophically as ADR count grows
(docs/adr-toolkit-audit-report.md §2.3 3.1, scoped down from "2,000
fixtures + CI regression tracking" -- no historical-baseline
infrastructure exists to make trend tracking meaningful; this instead
asserts a generous, one-shot wall-clock bound at a size well past any
observed real-world ADR count)."""
import time
from types import SimpleNamespace

from scripts.commands import index, search


def _write_adr(adr_dir, number, title):
    text = (
        "---\n"
        f"id: ADR-{number:04d}\n"
        f"title: {title}\n"
        "status: accepted\n"
        "date: 2026-01-01\n"
        "decision_makers: []\n"
        "related: []\n"
        "affected_paths: []\n"
        "tags:\n"
        "  - performance\n"
        "retrospective: false\n"
        "---\n\n"
        f"# {title}\n\nDecision body text for ADR {number}.\n"
    )
    (adr_dir / f"{number:04d}-decision-{number}.md").write_text(text, encoding="utf-8")


def test_search_and_index_handle_500_adrs_without_catastrophic_slowdown(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    for i in range(1, 501):
        _write_adr(adr_dir, i, f"Decision number {i}")

    started = time.monotonic()
    search_result = search.run(SimpleNamespace(
        dir=str(adr_dir), id=None, keyword="decision", tags=None, status=None, path=None, limit=None,
    ))
    index_result = index.run(SimpleNamespace(dir=str(adr_dir), root=str(tmp_path), locale=None))
    elapsed = time.monotonic() - started

    assert search_result["ok"] is True
    assert search_result["total"] == 500
    assert index_result["ok"] is True
    assert index_result["count"] == 500
    assert elapsed < 5.0, f"search+index over 500 ADRs took {elapsed:.2f}s -- investigate before real repos hit this scale"
