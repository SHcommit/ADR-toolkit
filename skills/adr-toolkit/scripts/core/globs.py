"""A **-aware glob matcher, stdlib-only.

Python's fnmatch/PurePath.match don't treat ** as "any number of path
segments" the way ArchUnit-style path rules need, so this implements just
that one extension on top of literal/*/? matching.
"""
import re


def match(pattern: str, path: str) -> bool:
    return re.match(_translate(pattern), path) is not None


def path_under(path: str, prefix: str) -> bool:
    """Directory-boundary prefix match: "src/db" governs "src/db/x.py" but
    not "src/db2/file.py"."""
    if path == prefix:
        return True
    return path.startswith(prefix.rstrip("/") + "/")


def _translate(pattern: str) -> str:
    parts = []
    i, n = 0, len(pattern)
    while i < n:
        char = pattern[i]
        if pattern[i:i + 2] == "**":
            if i + 2 < n and pattern[i + 2] == "/":
                parts.append(r"(?:.*/)?")
                i += 3
            else:
                parts.append(r".*")
                i += 2
        elif char == "*":
            parts.append(r"[^/]*")
            i += 1
        elif char == "?":
            parts.append(r"[^/]")
            i += 1
        else:
            parts.append(re.escape(char))
            i += 1
    return "^" + "".join(parts) + "$"
