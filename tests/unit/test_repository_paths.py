"""Tests for resolve_from_root's boundary enforcement
(docs/adr-toolkit-audit-report.md §2.2 2.3)."""

import pytest

from scripts.core.repository_paths import PathEscapesRootError, resolve_from_root


def test_relative_path_under_root_resolves_normally(tmp_path):
    result = resolve_from_root(tmp_path, "docs/decisions")
    assert result == tmp_path / "docs/decisions"


def test_absolute_path_is_returned_unchanged_even_outside_root(tmp_path):
    outside = tmp_path.parent / "somewhere-else"
    result = resolve_from_root(tmp_path, outside)
    assert result == outside


def test_relative_path_escaping_root_is_rejected(tmp_path):
    with pytest.raises(PathEscapesRootError):
        resolve_from_root(tmp_path, "../../etc/cron.d")


def test_relative_path_escaping_root_via_nested_traversal_is_rejected(tmp_path):
    with pytest.raises(PathEscapesRootError):
        resolve_from_root(tmp_path, "docs/../../outside")


def test_dot_path_resolves_to_root_itself(tmp_path):
    result = resolve_from_root(tmp_path, ".")
    assert result.resolve() == tmp_path.resolve()
