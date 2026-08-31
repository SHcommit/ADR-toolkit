from pathlib import Path

import pytest

from scripts.core import identifiers


def test_parse_filename_extracts_id_and_slug():
    assert identifiers.parse_filename("0003-use-provider-port.md") == (3, "use-provider-port")


def test_parse_filename_rejects_non_matching_names():
    assert identifiers.parse_filename("README.md") is None
    assert identifiers.parse_filename("3-too-short.md") is None


def test_next_id_is_one_past_the_highest_existing(tmp_path):
    (tmp_path / "0001-a.md").write_text("x", encoding="utf-8")
    (tmp_path / "0003-b.md").write_text("x", encoding="utf-8")
    assert identifiers.next_id(tmp_path) == 4


def test_next_id_starts_at_one_for_empty_directory(tmp_path):
    assert identifiers.next_id(tmp_path) == 1


def test_format_filename_zero_pads_to_four_digits():
    assert identifiers.format_filename(7, "use-kafka") == "0007-use-kafka.md"


def test_slugify_lowercases_and_hyphenates():
    assert identifiers.slugify("Use Kafka for Domain Events!") == "use-kafka-for-domain-events"


def test_non_ascii_title_uses_deterministic_fallback():
    assert identifiers.slug_for_title("결제 시스템 분리", None) == "decision"


def test_agent_semantic_slug_wins_for_non_ascii_title():
    assert identifiers.slug_for_title(
        "결제 시스템 분리", "separate-payment-system"
    ) == "separate-payment-system"


@pytest.mark.parametrize("slug", ["Bad Slug", "한글", "../escape", "two--hyphens"])
def test_invalid_explicit_slug_is_rejected(slug):
    with pytest.raises(ValueError):
        identifiers.validate_slug(slug)


def test_find_by_number_locates_matching_file(tmp_path):
    (tmp_path / "0003-use-kafka.md").write_text("x", encoding="utf-8")
    found = identifiers.find_by_number(tmp_path, 3)
    assert found is not None
    assert found.name == "0003-use-kafka.md"


def test_find_by_number_returns_none_when_missing(tmp_path):
    assert identifiers.find_by_number(tmp_path, 7) is None
