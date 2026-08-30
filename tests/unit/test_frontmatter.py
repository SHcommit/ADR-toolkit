import pytest

from scripts.core import frontmatter as fm


def test_parse_extracts_scalars_lists_and_body():
    text = (
        "---\n"
        "id: ADR-0003\n"
        "title: Use a provider port\n"
        "status: accepted\n"
        "date: 2026-08-29\n"
        "decision_makers:\n"
        "  - Yangseunghyeon\n"
        "related: []\n"
        "affected_paths:\n"
        "  - src/providers/\n"
        "  - src/core/ports/\n"
        "tags:\n"
        "  - architecture\n"
        "retrospective: false\n"
        "---\n"
        "\n"
        "# Use a provider port\n"
        "\n"
        "Body content.\n"
    )
    data, body = fm.parse(text)

    assert data["id"] == "ADR-0003"
    assert data["decision_makers"] == ["Yangseunghyeon"]
    assert data["affected_paths"] == ["src/providers/", "src/core/ports/"]
    assert data["retrospective"] is False
    assert body.strip().startswith("# Use a provider port")


def test_parse_raises_without_frontmatter_block():
    with pytest.raises(fm.FrontmatterError):
        fm.parse("# No frontmatter here\n")


def test_serialize_round_trips_through_parse():
    data = {
        "id": "ADR-0001",
        "title": "Record architecture decisions",
        "status": "accepted",
        "date": "2026-08-29",
        "decision_makers": [],
        "related": [],
        "affected_paths": ["docs/decisions/"],
        "tags": ["process"],
        "retrospective": False,
    }
    text = fm.serialize(data, "# Record architecture decisions\n\nBody.\n")
    parsed_data, parsed_body = fm.parse(text)

    assert parsed_data == data
    assert parsed_body.strip() == "# Record architecture decisions\n\nBody."
