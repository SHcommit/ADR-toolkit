"""Atomic, lock-protected file writes for ADR Toolkit's mutating commands.

Every command that writes ADR/exception files must hold `adr_directory_lock`
across its read-compute-write sequence (ID allocation, existence checks) and
write file contents through `atomic_write_text` -- never `Path.write_text`
directly. This closes the TOCTOU window between "compute next ID" and
"create file" under concurrent invocation, and guarantees a process killed
mid-write leaves the previous valid file in place rather than a truncated
one.
"""
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

if sys.platform == "win32":
    import msvcrt

    def _lock(fd: int) -> None:
        msvcrt.locking(fd, msvcrt.LK_LOCK, 1)

    def _unlock(fd: int) -> None:
        try:
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
else:
    import fcntl

    def _lock(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_EX)

    def _unlock(fd: int) -> None:
        fcntl.flock(fd, fcntl.LOCK_UN)


def atomic_write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)  # atomic rename on both POSIX and Windows
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


@contextmanager
def adr_directory_lock(directory: Path):
    """Serialize ID allocation + writes for one ADR/exceptions directory
    across processes. The lock file lives inside `directory` itself so a
    fresh clone or a brand-new `docs/decisions/` needs no extra setup."""
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / ".adr-toolkit.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
    try:
        _lock(fd)
        yield
    finally:
        _unlock(fd)
        os.close(fd)
