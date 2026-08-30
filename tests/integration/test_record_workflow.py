import json
import shutil
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "record_existing_adr"
ADR_PY = Path(__file__).resolve().parent.parent.parent / "skills" / "adr-toolkit" / "scripts" / "adr.py"


def _run(args, cwd):
    command = [sys.executable, str(ADR_PY), *args]
    result = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True,
    )
    assert result.returncode == 0, (
        f"CLI command failed: {' '.join(command)}\n"
        f"cwd: {cwd}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"CLI command did not return JSON: {' '.join(command)}\n"
            f"cwd: {cwd}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        ) from exc
    assert isinstance(payload, dict), (
        f"CLI command returned a non-object JSON payload: {' '.join(command)}\n"
        f"cwd: {cwd}\npayload: {payload!r}\nstderr:\n{result.stderr}"
    )
    assert payload.get("ok") is True, (
        f"CLI command reported failure: {' '.join(command)}\n"
        f"cwd: {cwd}\npayload: {payload!r}\nstderr:\n{result.stderr}"
    )
    return payload


def _status_section(readme, status):
    marker = f"### {status}\n"
    start = readme.index(marker) + len(marker)
    status_block = readme[start:readme.index("## By tag", start)]
    next_status = status_block.find("\n### ")
    return status_block if next_status == -1 else status_block[:next_status]


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
    superseded = _status_section(readme, "Superseded")
    accepted = _status_section(readme, "Accepted")
    assert "ADR-0001" in superseded
    assert "ADR-0002" not in superseded
    assert "ADR-0002" in accepted
    assert "ADR-0001" not in accepted
