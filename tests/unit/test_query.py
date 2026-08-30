from scripts.core.query import (
    matches_keyword,
    matches_paths_exact,
    matches_tags_any,
    path_governed_by,
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
