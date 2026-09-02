"""Atomic, lock-protected file writes for ADR Toolkit's mutating commands.

Every command that writes ADR/exception files must hold `adr_directory_lock`
across its read-compute-write sequence (ID allocation, existence checks) and
write file contents through `atomic_write_text` -- never `Path.write_text`
directly. This closes the TOCTOU window between "compute next ID" and
"create file" under concurrent invocation, and guarantees a process killed
mid-write leaves the previous valid file in place rather than a truncated
one.
"""
import json
import os
import signal
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from types import FrameType

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


LOCK_FILENAME = ".adr-toolkit.lock"
STALE_LOCK_TIMEOUT_SECONDS = 600.0


def is_lock_stale(lock_path: Path, max_age_seconds: float = STALE_LOCK_TIMEOUT_SECONDS) -> bool:
    """Check whether a lock file is stale based on file modification time or lock timestamp metadata."""
    if not lock_path.exists():
        return False
    try:
        mtime = lock_path.stat().st_mtime
        if time.time() - mtime > max_age_seconds:
            return True
        content = lock_path.read_text(encoding="utf-8").strip()
        if content:
            data = json.loads(content)
            ts = data.get("timestamp")
            if isinstance(ts, (int, float)) and time.time() - ts > max_age_seconds:
                return True
    except (OSError, json.JSONDecodeError, ValueError):
        pass
    return False


def break_stale_lock(directory: Path, max_age_seconds: float = STALE_LOCK_TIMEOUT_SECONDS) -> bool:
    """Check and remove a stale lock file or stale lock directory in `directory`."""
    lock_path = Path(directory) / LOCK_FILENAME
    if is_lock_stale(lock_path, max_age_seconds):
        try:
            lock_path.unlink(missing_ok=True)
            return True
        except OSError:
            pass
    return False


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
def _trap_signals() -> Iterator[None]:
    """Register temporary SIGINT and SIGTERM signal traps to ensure cleanup runs on interrupts."""
    old_sigint = None
    old_sigterm = None

    def _on_signal(signum: int, frame: Any) -> None:
        if signum == signal.SIGINT:
            raise KeyboardInterrupt("Interrupted by SIGINT")
        raise SystemExit(128 + signum)


    try:
        if threading_is_main_thread():
            try:
                old_sigint = signal.signal(signal.SIGINT, _on_signal)
                old_sigterm = signal.signal(signal.SIGTERM, _on_signal)
            except (ValueError, OSError):
                pass
        yield
    finally:
        if threading_is_main_thread():
            if old_sigint is not None:
                try:
                    signal.signal(signal.SIGINT, old_sigint)
                except (ValueError, OSError):
                    pass
            if old_sigterm is not None:
                try:
                    signal.signal(signal.SIGTERM, old_sigterm)
                except (ValueError, OSError):
                    pass


def threading_is_main_thread() -> bool:
    import threading
    return threading.current_thread() is threading.main_thread()


@contextmanager
def adr_directory_lock(directory: Path) -> Iterator[None]:
    """Serialize ID allocation + writes for one ADR/exceptions directory
    across processes. Automatically breaks stale locks if held longer than STALE_LOCK_TIMEOUT_SECONDS."""
    directory.mkdir(parents=True, exist_ok=True)
    lock_path = directory / LOCK_FILENAME

    # Clean up stale locks before acquiring
    break_stale_lock(directory)

    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
    with _trap_signals():
        try:
            _lock(fd)
            # Write timestamp and PID metadata
            try:
                os.ftruncate(fd, 0)
                os.lseek(fd, 0, os.SEEK_SET)
                metadata = json.dumps({"pid": os.getpid(), "timestamp": time.time()})
                os.write(fd, metadata.encode("utf-8"))
            except OSError:
                pass
            yield
        finally:
            _unlock(fd)
            os.close(fd)

