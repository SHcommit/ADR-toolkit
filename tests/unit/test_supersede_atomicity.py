"""Proves SUPERSEDE's two-file update never leaves a torn file, and that
its existing rollback-on-failure behavior still works once writes go
through atomic_io (docs/adr-toolkit-audit-report.md, Top-3 #1)."""
from types import SimpleNamespace

import pytest

from scripts.commands import supersede


_OLD_ADR = (
    "---\n"
    "id: ADR-0001\n"
    "title: Old decision\n"
    "status: accepted\n"
    "date: 2026-01-01\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths: []\n"
    "tags: []\n"
    "retrospective: false\n"
    "---\n\n"
    "Body of the old decision.\n"
)

_NEW_ADR = (
    "---\n"
    "id: ADR-0002\n"
    "title: New decision\n"
    "status: accepted\n"
    "date: 2026-01-02\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths: []\n"
    "tags: []\n"
    "retrospective: false\n"
    "---\n\n"
    "Body of the new decision.\n"
)


def _write_fixture_adrs(adr_dir):
    adr_dir.mkdir(parents=True)
    old_file = adr_dir / "0001-old-decision.md"
    new_file = adr_dir / "0002-new-decision.md"
    old_file.write_text(_OLD_ADR, encoding="utf-8")
    new_file.write_text(_NEW_ADR, encoding="utf-8")
    return old_file, new_file


def test_old_file_is_rolled_back_when_second_write_fails(tmp_path, monkeypatch):
    adr_dir = tmp_path / "docs" / "decisions"
    old_file, new_file = _write_fixture_adrs(adr_dir)

    real_write = supersede.atomic_io.atomic_write_text
    calls = {"count": 0}

    def flaky_write(path, content, **kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise OSError("simulated disk failure")
        return real_write(path, content, **kwargs)

    monkeypatch.setattr(supersede.atomic_io, "atomic_write_text", flaky_write)

    with pytest.raises(OSError):
        supersede.run(SimpleNamespace(adr_number=1, by=2, dir=str(adr_dir), dry_run=False))

    assert old_file.read_text(encoding="utf-8") == _OLD_ADR
    assert calls["count"] == 3  # old write, failed new write, rollback write


def test_no_tmp_files_survive_a_successful_supersede(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    old_file, new_file = _write_fixture_adrs(adr_dir)

    result = supersede.run(SimpleNamespace(adr_number=1, by=2, dir=str(adr_dir), dry_run=False))

    assert result["ok"] is True
    assert list(adr_dir.glob("*.tmp")) == []
