from scripts.core.adr_directory import SKIP_FILES, iter_adr_files


def _touch(path, text="content"):
    path.write_text(text, encoding="utf-8")


def test_iter_adr_files_skips_readme_and_template(tmp_path):
    _touch(tmp_path / "README.md")
    _touch(tmp_path / "adr-template.md")
    _touch(tmp_path / "0001-decision.md")

    results = list(iter_adr_files(tmp_path))

    assert [path.name for path, _ in results] == ["0001-decision.md"]


def test_iter_adr_files_yields_parsed_id_and_slug(tmp_path):
    _touch(tmp_path / "0002-use-a-cache.md")

    ((path, parsed),) = list(iter_adr_files(tmp_path))

    assert path.name == "0002-use-a-cache.md"
    assert parsed == (2, "use-a-cache")


def test_iter_adr_files_yields_none_for_unparseable_filename(tmp_path):
    _touch(tmp_path / "not-an-adr.md")

    ((path, parsed),) = list(iter_adr_files(tmp_path))

    assert path.name == "not-an-adr.md"
    assert parsed is None


def test_iter_adr_files_sorted_by_filename(tmp_path):
    _touch(tmp_path / "0002-second.md")
    _touch(tmp_path / "0001-first.md")

    results = list(iter_adr_files(tmp_path))

    assert [path.name for path, _ in results] == ["0001-first.md", "0002-second.md"]


def test_skip_files_constant_matches_known_non_adr_filenames():
    assert SKIP_FILES == {"README.md", "adr-template.md"}
