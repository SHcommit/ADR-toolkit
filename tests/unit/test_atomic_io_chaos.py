"""Chaos test: a process killed mid-write must never leave a torn ADR file
(docs/adr-toolkit-audit-report.md §2.8 8.2 -- atomic_io's core guarantee,
proven here at the OS level rather than by simulating a raised exception)."""
import os
import signal
import sys
import time
from pathlib import Path

import pytest

from scripts.core import atomic_io


def _write_slowly_then_get_killed(path_str: str, ready_flag_str: str) -> None:
    path = Path(path_str)
    ready_flag = Path(ready_flag_str)
    original_replace = os.replace

    def paused_replace(src, dst):
        # Signal the parent that the temp file exists and we're about to
        # rename it over the real target -- the single most dangerous
        # instant for a non-atomic write scheme -- then stall long enough
        # that the parent's SIGKILL always arrives first.
        ready_flag.write_text("ready", encoding="utf-8")
        time.sleep(10)
        return original_replace(src, dst)

    os.replace = paused_replace  # child-process-only; fork gives us a private copy
    atomic_io.atomic_write_text(path, "new content that must never land")


@pytest.mark.skipif(sys.platform == "win32", reason="os.fork is POSIX-only")
def test_process_killed_mid_write_never_leaves_a_torn_file(tmp_path):
    target = tmp_path / "0001-decision.md"
    target.write_text("original valid content\n", encoding="utf-8")
    ready_flag = tmp_path / "ready.flag"

    pid = os.fork()
    if pid == 0:
        try:
            _write_slowly_then_get_killed(str(target), str(ready_flag))
        finally:
            os._exit(1)  # should never actually reach here

    deadline = time.monotonic() + 5
    while not ready_flag.exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert ready_flag.exists(), "child never reached its pre-rename pause"

    os.kill(pid, signal.SIGKILL)
    os.waitpid(pid, 0)

    assert target.read_text(encoding="utf-8") == "original valid content\n"
