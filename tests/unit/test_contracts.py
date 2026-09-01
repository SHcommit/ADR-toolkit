"""Tests that core/contracts.py's TypedDicts describe real command output
shapes (docs/adr-toolkit-audit-report.md §2.4 4.1)."""
import subprocess
from types import SimpleNamespace

from scripts.commands import check, create
from scripts.core import contracts


def test_create_dry_run_result_matches_contract_keys(tmp_path):
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(
        '{"title": "Use Kafka", "status": "proposed", "body": "Body."}',
        encoding="utf-8",
    )
    args = SimpleNamespace(
        input=str(draft_path), interactive=False, dir="docs/decisions",
        root=str(tmp_path), locale=None, slug=None, dry_run=True,
    )
    result = create.run(args)

    contract_keys = set(contracts.CreateResult.__annotations__)
    assert set(result.keys()) <= contract_keys, (
        f"create.run() returned keys not in contracts.CreateResult: "
        f"{set(result.keys()) - contract_keys}"
    )


def test_check_result_with_no_adrs_matches_contract_keys(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)

    result = check.run(SimpleNamespace(root=str(tmp_path), dir=str(adr_dir), staged=False, since=None))

    assert result["ok"] is True
    contract_keys = set(contracts.CheckResult.__annotations__)
    assert set(result.keys()) <= contract_keys, (
        f"check.run() returned keys not in contracts.CheckResult: "
        f"{set(result.keys()) - contract_keys}"
    )
