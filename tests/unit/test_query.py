from scripts.core.query import (
    matches_keyword,
    matches_paths_exact,
    matches_tags_any,
    path_governed_by,
    rank_key,
)


def test_matches_keyword_in_title():
    assert matches_keyword("cache", "Cache policy for reads", "irrelevant body") is True


def test_matches_keyword_in_body_only():
    assert matches_keyword("redis", "Cache policy", "We chose Redis for shared caching.") is True


def test_matches_keyword_case_insensitive():
    assert matches_keyword("REDIS", "Cache policy", "we chose redis") is True


def test_matches_keyword_absent_returns_false():
    assert matches_keyword("postgres", "Cache policy", "We chose Redis.") is False


def test_matches_tags_any_returns_overlap():
    assert matches_tags_any({"check", "cli"}, ["cli", "v0.2.0"]) == {"cli"}


def test_matches_tags_any_empty_when_no_overlap():
    assert matches_tags_any({"check"}, ["cli"]) == set()


def test_matches_paths_exact_returns_overlap():
    assert matches_paths_exact({"src/db/"}, ["src/db/", "src/api/"]) == {"src/db/"}


def test_matches_paths_exact_does_not_prefix_match():
    assert matches_paths_exact({"src/db/x.py"}, ["src/db/"]) == set()


def test_path_governed_by_true_for_nested_file():
    assert path_governed_by("src/db/x.py", ["src/db/"]) is True


def test_path_governed_by_false_when_no_affected_path_covers_it():
    assert path_governed_by("src/other/x.py", ["src/db/"]) is False


def test_path_governed_by_ignores_non_string_affected_paths():
    assert path_governed_by("src/db/x.py", ["src/db/", 42, None]) is True


def _entry(id_="ADR-0001", title="Cache policy", body="body text"):
    return {"id": id_, "title": title, "body": body}


def test_rank_key_exact_id_match_ranks_first():
    exact_id = _entry(id_="ADR-0007")
    title_match = _entry(id_="ADR-0001", title="ADR-0007 discussion")
    ranked = sorted([title_match, exact_id], key=lambda e: rank_key(e, "ADR-0007"))
    assert ranked[0]["id"] == "ADR-0007"


def test_rank_key_exact_title_ranks_above_title_substring():
    exact_title = _entry(id_="ADR-0001", title="cache")
    substring_title = _entry(id_="ADR-0002", title="cache policy for reads")
    ranked = sorted([substring_title, exact_title], key=lambda e: rank_key(e, "cache"))
    assert ranked[0]["id"] == "ADR-0001"


def test_rank_key_title_substring_ranks_above_body_only_match():
    title_match = _entry(id_="ADR-0001", title="redis caching", body="unrelated")
    body_match = _entry(id_="ADR-0002", title="unrelated title", body="uses redis internally")
    ranked = sorted([body_match, title_match], key=lambda e: rank_key(e, "redis"))
    assert ranked[0]["id"] == "ADR-0001"


def test_rank_key_ties_break_by_filename_for_determinism():
    a = _entry(id_="ADR-0002", title="cache", body="")
    b = _entry(id_="ADR-0001", title="cache", body="")
    ranked = sorted([a, b], key=lambda e: rank_key(e, "cache"))
    assert [e["id"] for e in ranked] == ["ADR-0001", "ADR-0002"]
