from scripts.core import globs


def test_exact_match():
    assert globs.match("src/events/producer.py", "src/events/producer.py")
    assert not globs.match("src/events/producer.py", "src/events/consumer.py")


def test_single_star_matches_within_one_segment():
    assert globs.match("src/events/*.py", "src/events/producer.py")
    assert not globs.match("src/events/*.py", "src/events/sub/producer.py")


def test_double_star_matches_across_segments():
    assert globs.match("src/features/**", "src/features/x.py")
    assert globs.match("src/features/**", "src/features/sub/y.py")
    assert not globs.match("src/features/**", "src/other/x.py")


def test_double_star_prefix_matches_any_depth():
    assert globs.match("**/test_*.py", "test_foo.py")
    assert globs.match("**/test_*.py", "src/deep/test_foo.py")
    assert not globs.match("**/test_*.py", "src/deep/foo_test.py")


def test_question_mark_matches_single_character():
    assert globs.match("src/adr-?.md", "src/adr-1.md")
    assert not globs.match("src/adr-?.md", "src/adr-10.md")


def test_path_under_matches_exact_path():
    assert globs.path_under("src/db", "src/db") is True


def test_path_under_matches_nested_path():
    assert globs.path_under("src/db/x.py", "src/db") is True


def test_path_under_matches_with_trailing_slash_prefix():
    assert globs.path_under("src/db/x.py", "src/db/") is True


def test_path_under_respects_directory_boundaries():
    assert globs.path_under("src/db2/file.py", "src/db") is False


def test_path_under_false_for_unrelated_path():
    assert globs.path_under("src/other/x.py", "src/db") is False
