"""Wrap `git diff` for CHECK: staged, uncommitted, or since-a-ref changes."""
import subprocess
from pathlib import Path


class _GitCommandError(RuntimeError):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def run(args) -> dict:
    root = Path(getattr(args, "root", ".")).resolve()

    repo_check = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True,
    )
    if repo_check.returncode != 0:
        return {
            "ok": False,
            "operation": "diff",
            "errors": [{"code": "NOT_A_GIT_REPO", "detail": repo_check.stderr.strip()}],
        }

    since = getattr(args, "since", None)
    # `since` is agent/user-controlled, so it must never be able to reach git
    # as an *option*. `--end-of-options` (git >= 2.24) forces everything after
    # it to be read as a revision/path, which keeps CHECK read-only: a value
    # like `--output=/tmp/PWNED` now fails as an unknown revision instead of
    # making `git diff` write a file. Options themselves must still precede
    # the marker, hence the options/range split.
    if getattr(args, "staged", False):
        mode, diff_options, range_args = "staged", ["--cached"], []
    elif since:
        mode, diff_options, range_args = "since", [], [f"{since}..HEAD"]
    else:
        mode, diff_options, range_args = "uncommitted", [], []

    name_status = subprocess.run(
        [
            "git", "-C", str(root), "-c", "core.quotePath=false", "diff",
            "--name-status", "-z", *diff_options, "--end-of-options", *range_args,
        ],
        capture_output=True, text=True,
    )
    if name_status.returncode != 0:
        code = "INVALID_REF" if mode == "since" else "GIT_DIFF_FAILED"
        return {"ok": False, "operation": "diff", "errors": [{"code": code, "detail": name_status.stderr.strip()}]}

    patch = subprocess.run(
        [
            "git", "-C", str(root), "-c", "core.quotePath=false", "diff",
            "--unified=0", *diff_options, "--end-of-options", *range_args,
        ],
        capture_output=True, text=True,
    )
    if patch.returncode != 0:
        code = "INVALID_REF" if mode == "since" else "GIT_DIFF_FAILED"
        return {
            "ok": False,
            "operation": "diff",
            "errors": [{"code": code, "detail": patch.stderr.strip()}],
        }

    files = _parse_name_status(name_status.stdout)
    _attach_line_content(files, patch.stdout)

    if mode == "uncommitted":
        try:
            files.extend(_untracked_files(root))
        except _GitCommandError as exc:
            return {
                "ok": False,
                "operation": "diff",
                "errors": [{"code": exc.code, "detail": exc.detail}],
            }

    return {"ok": True, "operation": "diff", "mode": mode, "ref": since, "files": files}


def _untracked_files(root: Path) -> list:
    # `git diff` never shows untracked files, but a brand-new file is exactly
    # the kind of change CHECK needs to see (e.g. a new module that violates
    # a forbidden_import rule) — surface it as if it were entirely "added".
    listing = subprocess.run(
        [
            "git", "-C", str(root), "ls-files", "--others",
            "--exclude-standard", "-z",
        ],
        capture_output=True, text=True,
    )
    if listing.returncode != 0:
        raise _GitCommandError(
            "GIT_LS_FILES_FAILED",
            listing.stderr.strip() or "git ls-files failed",
        )
    entries = []
    for rel_path in listing.stdout.split("\0"):
        if not rel_path.strip():
            continue
        try:
            content_lines = (root / rel_path).read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            content_lines = []
        entries.append({
            "path": rel_path,
            "change_type": "added",
            "added_lines": content_lines,
            "removed_lines": [],
        })
    return entries


def _parse_name_status(output: str) -> list:
    status_map = {"A": "added", "M": "modified", "D": "deleted"}
    files = []
    if "\0" in output:
        parts = output.split("\0")
        if parts and parts[-1] == "":
            parts.pop()
        index = 0
        while index < len(parts):
            status = parts[index]
            index += 1
            status_char = status[0]
            if status_char in {"R", "C"}:
                old_path, new_path = parts[index], parts[index + 1]
                index += 2
                files.extend([
                    _file_entry(old_path, "deleted"),
                    _file_entry(new_path, "added"),
                ])
            else:
                path = parts[index]
                index += 1
                files.append(_file_entry(path, status_map.get(status_char, "modified")))
        return files

    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status_char = parts[0][0]
        if status_char == "R" and len(parts) == 3:
            old_path, new_path = parts[1], parts[2]
            files.extend([
                _file_entry(old_path, "deleted"),
                _file_entry(new_path, "added"),
            ])
            continue
        path = parts[-1]
        files.append(_file_entry(path, status_map.get(status_char, "modified")))
    return files


def _file_entry(path: str, change_type: str) -> dict:
    return {
        "path": path,
        "change_type": change_type,
        "added_lines": [],
        "removed_lines": [],
    }


def _attach_line_content(files: list, patch_output: str) -> None:
    by_path = {f["path"]: f for f in files}
    removed_target = None
    added_target = None
    for line in patch_output.splitlines():
        if line.startswith("--- "):
            src = line[6:] if line.startswith("--- a/") else None
            removed_target = by_path.get(src) if src else None
            continue
        if line.startswith("+++ "):
            dst = line[6:] if line.startswith("+++ b/") else None
            added_target = by_path.get(dst) if dst else None
            continue
        if line.startswith("+"):
            if added_target is not None:
                added_target["added_lines"].append(line[1:])
        elif line.startswith("-"):
            if removed_target is not None:
                removed_target["removed_lines"].append(line[1:])
