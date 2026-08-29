import json
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "record_existing_adr"
ADR_PY = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit" / "scripts" / "adr.py"


def _run(args, cwd):
    result = subprocess.run(
        [sys.executable, str(ADR_PY), *args], cwd=cwd, capture_output=True, text=True,
    )
    assert result.returncode in (0, 1), result.stderr
    return json.loads(result.stdout)


def test_record_finds_related_scores_and_creates_new_adr(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(FIXTURE, repo)

    related_result = _run(["related", "--tags", "architecture", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert related_result["count"] == 1
    assert related_result["matches"][0]["id"] == "ADR-0001"

    scores_path = repo / "scores.json"
    scores_path.write_text(json.dumps({
        "reversal_cost": 2, "boundary_or_pattern_change": 2,
        "multi_developer_relevance": 2, "ops_security_data_impact": 1,
    }), encoding="utf-8")
    sig_result = _run(["significance", "--input", "scores.json", "--json"], cwd=repo)
    assert sig_result["classification"] == "recommended"

    draft_path = repo / "draft.json"
    draft_path.write_text(json.dumps({
        "title": "Use Kafka instead of RabbitMQ",
        "status": "accepted",
        "body": "# Use Kafka instead of RabbitMQ\n\nBody.\n",
        "related": ["ADR-0001"],
    }), encoding="utf-8")
    create_result = _run(["create", "--input", "draft.json", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert create_result["id"] == "ADR-0002"

    validate_result = _run(["validate", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert validate_result["ok"] is True
    assert validate_result["checked"] == 2

    supersede_result = _run(["supersede", "1", "--by", "2", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert supersede_result["ok"] is True

    old_text = (repo / "docs" / "decisions" / "0001-use-rabbitmq.md").read_text(encoding="utf-8")
    assert "status: superseded" in old_text
    assert "superseded_by: ADR-0002" in old_text

    new_text = (repo / "docs" / "decisions" / "0002-use-kafka-instead-of-rabbitmq.md").read_text(encoding="utf-8")
    assert "supersedes:\n  - ADR-0001" in new_text

    final_validate_result = _run(["validate", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert final_validate_result["ok"] is True
    assert final_validate_result["checked"] == 2

    index_result = _run(["index", "--dir", "docs/decisions", "--json"], cwd=repo)
    assert index_result["ok"] is True
    assert index_result["count"] == 2

    readme = (repo / "docs" / "decisions" / "README.md").read_text(encoding="utf-8")
    assert "ADR-0001" in readme
    assert "ADR-0002" in readme
    assert "### Superseded" in readme
    assert "### Accepted" in readme
