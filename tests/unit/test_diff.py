# tests/unit/test_diff.py
import subprocess
from types import SimpleNamespace

from scripts.commands import diff


def _git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _init_repo(tmp_path):
    _git(["init", "-q", "-b", "master"], tmp_path)
    _git(["config", "user.email", "test@example.com"], tmp_path)
    _git(["config", "user.name", "Test"], tmp_path)
    (tmp_path / "existing.py").write_text("x = 1\n", encoding="utf-8")
    _git(["add", "existing.py"], tmp_path)
    _git(["commit", "-q", "-m", "initial"], tmp_path)


def test_not_a_git_repo_returns_specific_error(tmp_path):
    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=False, uncommitted=False, since=None))
    assert result["ok"] is False
    assert result["errors"][0]["code"] == "NOT_A_GIT_REPO"


def test_uncommitted_mode_reports_added_and_removed_lines(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "existing.py").write_text("x = 1\nimport openai\n", encoding="utf-8")

    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=False, uncommitted=True, since=None))

    assert result["ok"] is True
    assert result["mode"] == "uncommitted"
    entry = next(f for f in result["files"] if f["path"] == "existing.py")
    assert entry["change_type"] == "modified"
    assert "import openai" in entry["added_lines"]


def test_staged_mode_only_sees_staged_changes(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "new_file.py").write_text("y = 2\n", encoding="utf-8")
    _git(["add", "new_file.py"], tmp_path)
    (tmp_path / "existing.py").write_text("unstaged change\n", encoding="utf-8")

    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=True, uncommitted=False, since=None))

    paths = {f["path"] for f in result["files"]}
    assert paths == {"new_file.py"}
    assert result["files"][0]["change_type"] == "added"


def test_since_ref_diffs_against_head(tmp_path):
    _init_repo(tmp_path)
    _git(["checkout", "-q", "-b", "feature"], tmp_path)
    (tmp_path / "existing.py").write_text("x = 1\nimport openai\n", encoding="utf-8")
    _git(["commit", "-q", "-am", "add import"], tmp_path)

    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=False, uncommitted=False, since="master"))

    assert result["ok"] is True
    assert result["mode"] == "since"
    assert result["ref"] == "master"
    entry = next(f for f in result["files"] if f["path"] == "existing.py")
    assert "import openai" in entry["added_lines"]


def test_invalid_ref_returns_specific_error(tmp_path):
    _init_repo(tmp_path)
    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=False, uncommitted=False, since="no-such-ref"))
    assert result["ok"] is False
    assert result["errors"][0]["code"] == "INVALID_REF"


def test_deleted_file_reports_removed_lines(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "existing.py").unlink()

    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=False, uncommitted=True, since=None))

    entry = next(f for f in result["files"] if f["path"] == "existing.py")
    assert entry["change_type"] == "deleted"
    assert "x = 1" in entry["removed_lines"]


def test_uncommitted_mode_includes_untracked_new_files(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "brand_new.py").write_text("import openai\n", encoding="utf-8")

    result = diff.run(SimpleNamespace(root=str(tmp_path), staged=False, uncommitted=True, since=None))

    entry = next(f for f in result["files"] if f["path"] == "brand_new.py")
    assert entry["change_type"] == "added"
    assert "import openai" in entry["added_lines"]


def test_since_value_cannot_smuggle_a_git_option_that_writes_a_file(tmp_path):
    """CHECK is read-only: a `--since` starting with `-` must not reach git as an option."""
    _init_repo(tmp_path)
    (tmp_path / "existing.py").write_text("x = 2\n", encoding="utf-8")
    target = tmp_path / "PWNED"

    result = diff.run(SimpleNamespace(
        root=str(tmp_path), staged=False, uncommitted=False, since=f"--output={target}",
    ))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "INVALID_REF"
    # git's `--output` writes to the literal argument, i.e. "<target>..HEAD".
    assert not target.exists()
    assert not (tmp_path / f"{target.name}..HEAD").exists()
