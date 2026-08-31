from pathlib import Path

from scripts.core import frontmatter as fm
from scripts.core.identifiers import parse_filename

REPO_ROOT = Path(__file__).resolve().parents[2]
ADR_DIR = REPO_ROOT / "docs/decisions"


def _repository_adrs():
    for path in sorted(ADR_DIR.glob("*.md")):
        if parse_filename(path.name) is None:
            continue
        data, body = fm.parse(path.read_text(encoding="utf-8"))
        yield path, data, body


def test_accepted_repository_adrs_name_a_decision_maker_and_locale():
    for path, data, _body in _repository_adrs():
        if data["status"] == "accepted":
            assert data["decision_makers"] == ["YangSeungHyun"], path.name
        assert data.get("locale") == "en", path.name


def test_retrospective_repository_adrs_separate_evidence_from_inference():
    entries = list(_repository_adrs())
    retrospective_ids = {
        data["id"] for _path, data, _body in entries if data["retrospective"]
    }
    assert retrospective_ids == {"ADR-0002", "ADR-0003", "ADR-0004"}

    for path, data, body in entries:
        if data["retrospective"]:
            assert "## Confirmed Evidence" in body, path.name
            assert "## Inferred Rationale" in body, path.name
            assert "## Unknown" in body, path.name


def test_repository_adrs_cover_their_governing_paths():
    required_paths = {
        "ADR-0002": {
            "skills/adr-toolkit/scripts/core/constraints.py",
            "skills/adr-toolkit/scripts/commands/diff.py",
            "skills/adr-toolkit/references/conflict-rules.md",
        },
        "ADR-0003": {
            ".adr-toolkit.json",
            "skills/adr-toolkit/SKILL.md",
            "skills/adr-toolkit/scripts/core/rendering.py",
        },
        "ADR-0004": {"adapters/", ".gitignore", ".claude-plugin/marketplace.json"},
        "ADR-0005": {"skills/adr-toolkit/VERSION", "scripts/sync_version.py"},
    }
    for path, data, _body in _repository_adrs():
        expected = required_paths.get(data["id"], set())
        assert expected <= set(data["affected_paths"]), path.name


def test_repository_adr_structure_matches_its_evidence_contract():
    entries = {data["id"]: (path, body) for path, data, body in _repository_adrs()}
    assert "* [ ]" not in entries["ADR-0001"][1]
    adr4_body = entries["ADR-0004"][1]
    assert "## Decision Drivers" in adr4_body
    assert "## Pros and Cons of the Options" in adr4_body
