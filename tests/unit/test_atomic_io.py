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
