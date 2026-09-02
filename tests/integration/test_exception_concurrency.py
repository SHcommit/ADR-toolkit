"""Proves exception creation is race-free under concurrent invocation, the
same class of bug as create.py (docs/adr-toolkit-audit-report.md §2.3 3.3)."""
import json
import multiprocessing
from pathlib import Path

from types import SimpleNamespace

from scripts.commands import exception as exception_cmd


def _create_exception(payload):
    root_str, index = payload
    root = Path(root_str)
    draft_path = root / f"draft-{index}.json"
    draft_path.write_text(
        json.dumps({
            "adr_id": "ADR-0001",
            "rule_id": "forbidden_import",
            "owner": f"owner-{index}",
            "reason": "test exception",
            "scope": ["src/**"],
            "expiry": "2099-01-01",
        }),
        encoding="utf-8",
    )
    args = SimpleNamespace(
        input=str(draft_path),
        dir="docs/decisions",
        root=root_str,
        dry_run=False,
    )
    return exception_cmd.run(args)


def test_concurrent_exception_creation_never_duplicates_ids(tmp_path):
    with multiprocessing.Pool(processes=8) as pool:
        results = pool.map(_create_exception, [(str(tmp_path), i) for i in range(20)])

    assert all(result["ok"] for result in results), results
    ids = [result["id"] for result in results]
    assert len(ids) == len(set(ids)), f"duplicate exception IDs allocated: {ids}"
