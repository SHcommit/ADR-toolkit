"""Tests for the ReDoS timeout guard on author-supplied CHECK patterns
(docs/adr-toolkit-audit-report.md, Top-3 #2)."""
import re
import sys
import time

import pytest

from scripts.rules import conflict


@pytest.mark.skipif(sys.platform == "win32", reason="SIGALRM guard is POSIX-only")
def test_guarded_search_raises_regex_timeout_on_pathological_pattern():
    regex = re.compile(r"(a+)+$")
    pathological_input = "a" * 35 + "!"

    started = time.monotonic()
    with pytest.raises(conflict.RegexTimeout):
        conflict._guarded_search(regex, pathological_input)
    elapsed = time.monotonic() - started

    assert elapsed < 1.0


def test_regex_timeout_is_a_re_error_so_check_py_catches_it():
    assert issubclass(conflict.RegexTimeout, re.error)


def test_guarded_search_still_matches_normal_patterns():
    regex = re.compile(r"forbidden_call\(")
    assert conflict._guarded_search(regex, "x = forbidden_call(1)") is not None
    assert conflict._guarded_search(regex, "x = 1") is None
