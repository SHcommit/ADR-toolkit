import subprocess

import pytest

from scripts.core import git_paths


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _init_repo(tmp_path):
    _git(["init", "-q", "-b", "master"], tmp_path)
    _git(["config", "user.email", "test@example.com"], tmp_path)
    _git(["config", "user.name", "Test"], tmp_path)
    (tmp_path / "existing.py").write_text("x = 1\n", encoding="utf-8")
    _git(["add", "existing.py"], tmp_path)
    _git(["commit", "-q", "-m", "initial"], tmp_path)


def test_existing_paths_include_tracked_and_untracked_but_not_ignored(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("build/\n", encoding="utf-8")
    (tmp_path / "untracked.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "build").mkdir()
    (tmp_path / "build/generated.py").write_text("x = 1\n", encoding="utf-8")

    paths = git_paths.list_existing_paths(tmp_path)

    assert "existing.py" in paths
    assert "untracked.py" in paths
    assert "build/generated.py" not in paths


def test_git_path_listing_failure_includes_stderr(tmp_path, monkeypatch):
    def fail(command, **kwargs):
        return subprocess.CompletedProcess(command, 128, "", "not a repository")

    monkeypatch.setattr(git_paths.subprocess, "run", fail)

    with pytest.raises(git_paths.GitPathsError, match="not a repository"):
        git_paths.list_existing_paths(tmp_path)
