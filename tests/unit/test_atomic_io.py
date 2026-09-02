"""Tests for atomic, lock-protected file writes."""
import multiprocessing
import time
from pathlib import Path

from scripts.core import atomic_io


def test_atomic_write_text_creates_file_with_content(tmp_path):
    target = tmp_path / "note.txt"
    atomic_io.atomic_write_text(target, "hello world")
    assert target.read_text(encoding="utf-8") == "hello world"


def test_atomic_write_text_leaves_no_tmp_file_behind(tmp_path):
    target = tmp_path / "note.txt"
    atomic_io.atomic_write_text(target, "hello world")
    leftovers = list(tmp_path.glob(".note.txt.*.tmp"))
    assert leftovers == []


def test_atomic_write_text_replaces_existing_content(tmp_path):
    target = tmp_path / "note.txt"
    atomic_io.atomic_write_text(target, "first")
    atomic_io.atomic_write_text(target, "second")
    assert target.read_text(encoding="utf-8") == "second"


def test_atomic_write_text_creates_missing_parent_directories(tmp_path):
    target = tmp_path / "nested" / "dir" / "note.txt"
    atomic_io.atomic_write_text(target, "hello")
    assert target.read_text(encoding="utf-8") == "hello"


def _append_under_lock(payload):
    directory_str, log_path_str, worker_id = payload
    directory = Path(directory_str)
    log_path = Path(log_path_str)
    with atomic_io.adr_directory_lock(directory):
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"start {worker_id}\n")
        time.sleep(0.05)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"end {worker_id}\n")
    return worker_id


def test_adr_directory_lock_serializes_concurrent_workers(tmp_path):
    directory = tmp_path / "docs" / "decisions"
    directory.mkdir(parents=True)
    log_path = tmp_path / "order.log"
    log_path.write_text("", encoding="utf-8")

    with multiprocessing.Pool(processes=4) as pool:
        pool.map(
            _append_under_lock,
            [(str(directory), str(log_path), i) for i in range(4)],
        )

    lines = log_path.read_text(encoding="utf-8").splitlines()
    # Every "start N" must be immediately followed by "end N" -- the lock
    # forbids another worker's "start" from interleaving in between.
    assert len(lines) == 8
    for i in range(0, len(lines), 2):
        worker = lines[i].split()[1]
        assert lines[i] == f"start {worker}"
        assert lines[i + 1] == f"end {worker}"


def test_stale_lock_detection_and_break(tmp_path):
    directory = tmp_path / "docs" / "decisions"
    directory.mkdir(parents=True)
    lock_path = directory / atomic_io.LOCK_FILENAME

    # Fresh lock is not stale
    lock_path.write_text('{"pid": 1234, "timestamp": ' + str(time.time()) + "}", encoding="utf-8")
    assert not atomic_io.is_lock_stale(lock_path, max_age_seconds=600)
    assert not atomic_io.break_stale_lock(directory, max_age_seconds=600)

    # Stale lock (timestamp in past)
    old_time = time.time() - 1000
    lock_path.write_text('{"pid": 1234, "timestamp": ' + str(old_time) + "}", encoding="utf-8")
    assert atomic_io.is_lock_stale(lock_path, max_age_seconds=600)
    assert atomic_io.break_stale_lock(directory, max_age_seconds=600)
    assert not lock_path.exists()


def test_adr_directory_lock_writes_metadata(tmp_path):
    directory = tmp_path / "docs" / "decisions"
    directory.mkdir(parents=True)
    lock_path = directory / atomic_io.LOCK_FILENAME

    with atomic_io.adr_directory_lock(directory):
        assert lock_path.exists()
        content = lock_path.read_text(encoding="utf-8")
        assert "pid" in content
        assert "timestamp" in content

