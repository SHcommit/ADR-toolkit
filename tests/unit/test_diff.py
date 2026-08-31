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


def test_uncommitted_mode_preserves_unicode_untracked_path_and_content(tmp_path):
    _init_repo(tmp_path)
    unicode_path = tmp_path / "src" / "결제.py"
    unicode_path.parent.mkdir()
    unicode_path.write_text("import openai\n", encoding="utf-8")

    result = diff.run(SimpleNamespace(
        root=str(tmp_path), staged=False, uncommitted=True, since=None,
    ))

    entry = next(f for f in result["files"] if f["path"] == "src/결제.py")
    assert entry["change_type"] == "added"
    assert entry["added_lines"] == ["import openai"]


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


def test_patch_subprocess_failure_is_not_reported_as_clean(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    real_run = diff.subprocess.run
    diff_calls = 0

    def fake_run(command, **kwargs):
        nonlocal diff_calls
        if "diff" in command:
            diff_calls += 1
            if diff_calls == 2:
                return subprocess.CompletedProcess(command, 2, "", "patch failed")
        return real_run(command, **kwargs)

    monkeypatch.setattr(diff.subprocess, "run", fake_run)

    result = diff.run(SimpleNamespace(
        root=str(tmp_path), staged=False, uncommitted=True, since=None,
    ))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "GIT_DIFF_FAILED"
    assert "patch failed" in result["errors"][0]["detail"]


def test_untracked_listing_failure_is_not_reported_as_clean(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    real_run = diff.subprocess.run

    def fake_run(command, **kwargs):
        if "ls-files" in command:
            return subprocess.CompletedProcess(command, 2, "", "listing failed")
        return real_run(command, **kwargs)

    monkeypatch.setattr(diff.subprocess, "run", fake_run)

    result = diff.run(SimpleNamespace(
        root=str(tmp_path), staged=False, uncommitted=True, since=None,
    ))

    assert result["ok"] is False
    assert result["errors"][0]["code"] == "GIT_LS_FILES_FAILED"
    assert "listing failed" in result["errors"][0]["detail"]


def test_parse_rename_preserves_old_and_new_paths():
    files = diff._parse_name_status("R100\tsrc/old.py\tsrc/new.py\n")

    assert [(item["path"], item["change_type"]) for item in files] == [
        ("src/old.py", "deleted"),
        ("src/new.py", "added"),
    ]


def test_staged_rename_reports_deletion_and_addition(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src/old.py").write_text("one\ntwo\nthree\n", encoding="utf-8")
    _git(["add", "src/old.py"], tmp_path)
    _git(["commit", "-q", "-m", "add old path"], tmp_path)
    _git(["mv", "src/old.py", "src/new.py"], tmp_path)

    result = diff.run(SimpleNamespace(
        root=str(tmp_path), staged=True, uncommitted=False, since=None,
    ))

    changes = {(item["path"], item["change_type"]) for item in result["files"]}
    assert ("src/old.py", "deleted") in changes
    assert ("src/new.py", "added") in changes


def test_rename_patch_lines_are_attached_to_the_corresponding_path():
    files = diff._parse_name_status("R090\tsrc/old.py\tsrc/new.py\n")
    patch = (
        "diff --git a/src/old.py b/src/new.py\n"
        "--- a/src/old.py\n"
        "+++ b/src/new.py\n"
        "@@ -1 +1 @@\n"
        "-old value\n"
        "+new value\n"
    )

    diff._attach_line_content(files, patch)

    by_path = {item["path"]: item for item in files}
    assert by_path["src/old.py"]["removed_lines"] == ["old value"]
    assert by_path["src/new.py"]["added_lines"] == ["new value"]
