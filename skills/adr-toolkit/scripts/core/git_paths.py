"""List repository paths using Git's tracked and ignore semantics."""
import subprocess
from pathlib import Path


class GitPathsError(RuntimeError):
    """Git could not provide a trustworthy repository path inventory."""


def list_existing_paths(root: Path) -> set:
    result = subprocess.run(
        [
            "git", "-C", str(root), "ls-files", "--cached", "--others",
            "--exclude-standard",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GitPathsError(result.stderr.strip() or "git ls-files failed")
    return {line for line in result.stdout.splitlines() if line}
