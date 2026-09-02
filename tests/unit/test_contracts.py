"""Tests that core/contracts.py's TypedDicts describe real command output
shapes (docs/adr-toolkit-audit-report.md §2.4 4.1)."""
import json
import subprocess
from types import SimpleNamespace

from scripts.commands import (
    check,
    create,
    diff,
    discover,
    exception,
    graph,
    index,
    init,
    preflight,
    related,
    search,
    significance,
    status,
    supersede,
    validate,
)
from scripts.core import contracts


def _assert_keys_subset(result, contract, label):
    contract_keys = set(contract.__annotations__)
    assert set(result.keys()) <= contract_keys, (
        f"{label} returned keys not in {contract.__name__}: {set(result.keys()) - contract_keys}"
    )


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
    _assert_keys_subset(result, contracts.CheckResult, "check.run()")


def test_preflight_result_matches_contract_keys(tmp_path):
    result = preflight.run(SimpleNamespace(root=str(tmp_path)))
    assert result["ok"] is True
    _assert_keys_subset(result, contracts.PreflightResult, "preflight.run()")


def test_discover_result_matches_contract_keys(tmp_path):
    result = discover.run(SimpleNamespace(root=str(tmp_path)))
    assert result["ok"] is True
    _assert_keys_subset(result, contracts.DiscoverResult, "discover.run()")


def test_init_dry_run_result_matches_contract_keys(tmp_path):
    result = init.run(SimpleNamespace(dir="docs/decisions", root=str(tmp_path), locale=None, dry_run=True))
    assert result["ok"] is True
    _assert_keys_subset(result, contracts.InitResult, "init.run()")


def test_index_result_matches_contract_keys(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    result = index.run(SimpleNamespace(dir=str(adr_dir), root=str(tmp_path), locale=None))
    assert result["ok"] is True
    _assert_keys_subset(result, contracts.IndexResult, "index.run()")


def test_related_result_matches_contract_keys(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    result = related.run(SimpleNamespace(dir=str(adr_dir), paths=None, tags=None, keyword=None))
    assert result["ok"] is True
    _assert_keys_subset(result, contracts.RelatedResult, "related.run()")


def test_significance_result_matches_contract_keys(tmp_path):
    input_path = tmp_path / "scores.json"
    input_path.write_text(json.dumps({
        "reversal_cost": 0, "alternatives_considered": 0, "quality_attribute_impact": 0,
        "boundary_or_pattern_change": 0, "multi_developer_relevance": 0,
        "ops_security_data_impact": 0, "future_rationale_query_likelihood": 0,
    }), encoding="utf-8")
    result = significance.run(SimpleNamespace(input=str(input_path)))
    assert result["ok"] is True
    _assert_keys_subset(result, contracts.SignificanceResult, "significance.run()")


def test_validate_result_matches_contract_keys(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    result = validate.run(SimpleNamespace(dir=str(adr_dir), root=str(tmp_path)))
    assert result["ok"] is True
    _assert_keys_subset(result, contracts.ValidateResult, "validate.run()")


_STATUS_FIXTURE_ADR = (
    "---\n"
    "id: ADR-0001\n"
    "title: A decision\n"
    "status: proposed\n"
    "date: 2026-01-01\n"
    "decision_makers: []\n"
    "related: []\n"
    "affected_paths: []\n"
    "tags: []\n"
    "retrospective: false\n"
    "---\n\nBody.\n"
)


def test_status_dry_run_result_matches_contract_keys(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-a-decision.md").write_text(_STATUS_FIXTURE_ADR, encoding="utf-8")
    result = status.run(SimpleNamespace(adr_number=1, to="accepted", dir=str(adr_dir), dry_run=True))
    assert result["ok"] is True
    _assert_keys_subset(result, contracts.StatusResult, "status.run()")


_SUPERSEDE_OLD_ADR = (
    "---\nid: ADR-0001\ntitle: Old\nstatus: accepted\ndate: 2026-01-01\n"
    "decision_makers: []\nrelated: []\naffected_paths: []\ntags: []\n"
    "retrospective: false\n---\n\nBody.\n"
)
_SUPERSEDE_NEW_ADR = (
    "---\nid: ADR-0002\ntitle: New\nstatus: accepted\ndate: 2026-01-02\n"
    "decision_makers: []\nrelated: []\naffected_paths: []\ntags: []\n"
    "retrospective: false\n---\n\nBody.\n"
)


def test_supersede_dry_run_result_matches_contract_keys(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-old.md").write_text(_SUPERSEDE_OLD_ADR, encoding="utf-8")
    (adr_dir / "0002-new.md").write_text(_SUPERSEDE_NEW_ADR, encoding="utf-8")
    result = supersede.run(SimpleNamespace(adr_number=1, by=2, dir=str(adr_dir), dry_run=True))
    assert result["ok"] is True
    _assert_keys_subset(result, contracts.SupersedeResult, "supersede.run()")


def test_diff_result_matches_contract_keys(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=False, since=None))
    assert result["ok"] is True
    _assert_keys_subset(result, contracts.DiffResult, "diff.run()")


def test_exception_dry_run_result_matches_contract_keys(tmp_path):
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps({
        "adr_id": "ADR-0001", "rule_id": "r", "owner": "o", "reason": "r",
        "scope": ["src/**"], "expiry": "2099-01-01",
    }), encoding="utf-8")
    result = exception.run(SimpleNamespace(
        input=str(draft_path), dir="docs/decisions", root=str(tmp_path), dry_run=True,
    ))
    assert result["ok"] is True
    _assert_keys_subset(result, contracts.ExceptionResult, "exception.run()")


def test_graph_result_matches_contract_keys(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    result = graph.run(SimpleNamespace(dir=str(adr_dir), root=str(tmp_path), format="both", output=None))
    assert result["ok"] is True
    _assert_keys_subset(result, contracts.GraphResult, "graph.run()")


def test_search_result_matches_contract_keys(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    result = search.run(SimpleNamespace(
        dir=str(adr_dir), id=None, keyword=None, tags=None, status=None, path=None, limit=None,
    ))
    assert result["ok"] is True
    _assert_keys_subset(result, contracts.SearchResult, "search.run()")
