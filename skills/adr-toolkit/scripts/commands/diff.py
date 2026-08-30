"""Wrap `git diff` for CHECK: staged, uncommitted, or since-a-ref changes."""
import subprocess
from pathlib import Path


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
        ["git", "-C", str(root), "diff", "--name-status", *diff_options, "--end-of-options", *range_args],
        capture_output=True, text=True,
    )
    if name_status.returncode != 0:
        code = "INVALID_REF" if since else "GIT_DIFF_FAILED"
        return {"ok": False, "operation": "diff", "errors": [{"code": code, "detail": name_status.stderr.strip()}]}

    patch = subprocess.run(
        ["git", "-C", str(root), "diff", "--unified=0", *diff_options, "--end-of-options", *range_args],
        capture_output=True, text=True,
    )

    files = _parse_name_status(name_status.stdout)
    _attach_line_content(files, patch.stdout)

    if mode == "uncommitted":
        files.extend(_untracked_files(root))

    return {"ok": True, "operation": "diff", "mode": mode, "ref": since, "files": files}


def _untracked_files(root: Path) -> list:
    # `git diff` never shows untracked files, but a brand-new file is exactly
    # the kind of change CHECK needs to see (e.g. a new module that violates
    # a forbidden_import rule) — surface it as if it were entirely "added".
    listing = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True,
    )
    entries = []
    for rel_path in listing.stdout.splitlines():
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
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status_char, path = parts[0][0], parts[-1]
        files.append({
            "path": path,
            "change_type": status_map.get(status_char, "modified"),
            "added_lines": [],
            "removed_lines": [],
        })
    return files


def _attach_line_content(files: list, patch_output: str) -> None:
    by_path = {f["path"]: f for f in files}
    current = None
    for line in patch_output.splitlines():
        if line.startswith("--- "):
            src = line[6:] if line.startswith("--- a/") else None
            current = by_path.get(src) if src else current
            continue
        if line.startswith("+++ "):
            dst = line[6:] if line.startswith("+++ b/") else None
            current = by_path.get(dst) if dst else current
            continue
        if current is None:
            continue
        if line.startswith("+"):
            current["added_lines"].append(line[1:])
        elif line.startswith("-"):
            current["removed_lines"].append(line[1:])
