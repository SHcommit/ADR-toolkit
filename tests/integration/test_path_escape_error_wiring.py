"""Proves every resolve_from_root call site converts a path-escape attempt
into a structured PATH_ESCAPES_ROOT error instead of an opaque
INTERNAL_ERROR (docs/adr-toolkit-audit-report.md §2.2 2.3, closing a gap
left by the High-priority pass)."""
import json
import subprocess
from types import SimpleNamespace

from scripts.commands import check, create, exception, graph, index, init, validate

ESCAPING_DIR = "../../outside"


def _assert_rejected(result, operation):
    assert result["ok"] is False
    assert result["operation"] == operation
    assert result["errors"][0]["code"] == "PATH_ESCAPES_ROOT"


def test_init_rejects_escaping_dir(tmp_path):
    result = init.run(SimpleNamespace(dir=ESCAPING_DIR, root=str(tmp_path), locale=None, dry_run=False))
    _assert_rejected(result, "init")


def test_index_rejects_escaping_dir(tmp_path):
    result = index.run(SimpleNamespace(dir=ESCAPING_DIR, root=str(tmp_path), locale=None))
    _assert_rejected(result, "index")


def test_validate_rejects_escaping_dir(tmp_path):
    result = validate.run(SimpleNamespace(dir=ESCAPING_DIR, root=str(tmp_path)))
    _assert_rejected(result, "validate")


def test_check_rejects_escaping_dir(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    result = check.run(SimpleNamespace(dir=ESCAPING_DIR, root=str(tmp_path), staged=False, since=None))
    _assert_rejected(result, "check")


def test_graph_rejects_escaping_dir(tmp_path):
    result = graph.run(SimpleNamespace(dir=ESCAPING_DIR, root=str(tmp_path), format="both", output=None))
    _assert_rejected(result, "graph")


def test_graph_rejects_escaping_output(tmp_path):
    adr_dir = tmp_path / "docs" / "decisions"
    adr_dir.mkdir(parents=True)
    result = graph.run(SimpleNamespace(
        dir=str(adr_dir), root=str(tmp_path), format="mermaid", output=ESCAPING_DIR,
    ))
    _assert_rejected(result, "graph")


def test_create_rejects_escaping_dir(tmp_path):
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(
        json.dumps({"title": "Use Kafka", "status": "proposed", "body": "Body."}),
        encoding="utf-8",
    )
    result = create.run(SimpleNamespace(
        input=str(draft_path), interactive=False, dir=ESCAPING_DIR, root=str(tmp_path),
        locale=None, slug=None, dry_run=False,
    ))
    _assert_rejected(result, "create")


def test_exception_rejects_escaping_dir(tmp_path):
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(
        json.dumps({
            "adr_id": "ADR-0001", "rule_id": "r", "owner": "o", "reason": "r",
            "scope": ["src/**"], "expiry": "2099-01-01",
        }),
        encoding="utf-8",
    )
    result = exception.run(SimpleNamespace(input=str(draft_path), dir=ESCAPING_DIR, root=str(tmp_path), dry_run=False))
    _assert_rejected(result, "exception")
