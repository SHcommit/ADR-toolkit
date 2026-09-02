"""Proves ADR creation is race-free under concurrent invocation (the
Top-3 #1 finding in docs/adr-toolkit-audit-report.md)."""
import json
import multiprocessing
from pathlib import Path
from types import SimpleNamespace

from scripts.commands import create


def _create_one(payload):
    adr_dir_str, index = payload
    adr_dir = Path(adr_dir_str)
    draft_path = adr_dir.parent / f"draft-{index}.json"
    draft_path.write_text(
        json.dumps({"title": f"Decision {index}", "status": "proposed", "body": "Body text."}),
        encoding="utf-8",
    )
    args = SimpleNamespace(
        input=str(draft_path),
        interactive=False,
        dir=adr_dir_str,
        root=".",
        locale=None,
        slug=f"decision-{index}",
        dry_run=False,
    )
    return create.run(args)


def test_concurrent_create_never_duplicates_ids(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)

    with multiprocessing.Pool(processes=8) as pool:
        results = pool.map(_create_one, [(str(adr_dir), i) for i in range(20)])

    assert all(result["ok"] for result in results), results
    ids = [result["id"] for result in results]
    assert len(ids) == len(set(ids)), f"duplicate IDs allocated: {ids}"
