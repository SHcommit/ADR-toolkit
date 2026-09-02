---
id: ADR-0013
title: Two-stage ReDoS defense for CHECK's author-supplied constraint regexes
status: accepted
date: 2026-09-01
locale: en
decision_makers:
  - YangSeungHyun
related:
  - ADR-0002
  - ADR-0007
  - ADR-0008
affected_paths:
  - skills/adr-toolkit/scripts/rules/conflict.py
  - skills/adr-toolkit/scripts/core/constraints.py
  - tests/unit/test_conflict.py
  - tests/unit/test_constraints.py
tags:
  - security
  - check
  - core
  - v0.3.0
retrospective: false
---

# Two-stage ReDoS defense for CHECK's author-supplied constraint regexes

## Context and Problem Statement

`forbidden_import` and `dependency_forbidden` constraint rules let an ADR author write an arbitrary regular expression in the `pattern` field, which `rules/conflict.py` then matches against every added line in a diff. Because the author controls this regex, an accidental or malicious catastrophic-backtracking pattern (e.g. `(a+)+$`) can make `re.search()` hang for an unbounded time on ordinary input, stalling CHECK -- including in CI, where a single hung run occupies a runner until it times out.

## Decision Drivers

* CI runs on ubuntu, macOS, and Windows; a defense that only works on one platform family leaves the others fully exposed.
* Python's standard library has no regex execution timeout; the usual approach (`signal.alarm`/`setitimer`) is POSIX-only.
* `commands/check.py` already downgrades a `re.error` at pattern-compile time to a `BAD_CONSTRAINTS` warning; reusing that path avoids adding a new failure mode.
* No third-party regex engine (e.g. `re2`) may be introduced, per this project's zero-dependency constraint.

## Considered Options

* Replace Python's `re` with a linear-time third-party engine
* Run each regex match in a separate subprocess and kill it on timeout
* POSIX `SIGALRM`/`setitimer` runtime timeout only
* Runtime timeout (POSIX) plus a platform-independent static rejection of the most common catastrophic-backtracking shape at parse time

## Decision Outcome

Chosen option: **runtime timeout plus static rejection**, because a single platform-only defense leaves one whole platform family (Windows) with zero protection, and the static check closes that gap without a new dependency or a per-line subprocess.

`rules/conflict.py` adds `RegexTimeout(re.error)` and `_guarded_search()`, which wraps `regex.search()` in a 0.25s `SIGALRM` timeout on POSIX; because `RegexTimeout` subclasses `re.error`, `check.py`'s existing `except re.error` handling downgrades a timeout to `BAD_CONSTRAINTS` with no code change there. Separately, `core/constraints.py` adds `_reject_if_redos_prone()`, a static check that rejects any `forbidden_import`/`dependency_forbidden` pattern containing a quantified group whose own body ends in a quantifier (e.g. `(a+)+`, `(a*)*`) at parse time, before the pattern ever reaches `re.compile()`. This check is scoped to only those two rule kinds; `required_path`/`forbidden_path` treat `pattern` as a glob via `core/globs.py`, which cannot produce catastrophic backtracking, so applying the same check there would be a false positive.

### Consequences

* Good: a catastrophic-backtracking pattern like `(a+)+$` is now interrupted well under 1 second on POSIX, and rejected outright at parse time on every platform if it matches the nested-quantifier shape.
* Good: no new dependency, and no change needed in `check.py`'s existing error handling.
* Bad: the static check is a heuristic for the single most common ReDoS shape, not a general detector -- alternation-based patterns such as `(a|a)*` are not caught, and on Windows (no `SIGALRM`) the static check is the *only* defense such a pattern would face.

### Confirmation

`tests/unit/test_conflict.py` verifies `(a+)+$` is interrupted by the timeout guard; `tests/unit/test_constraints.py` verifies a nested-quantifier pattern is rejected before `re.compile()` is ever called (via a monkeypatched `re.compile` that asserts it is not invoked), and that the real, already-dogfooded `ADR-0011` constraints block still validates cleanly.

## Pros and Cons of the Options

### Third-party linear-time regex engine

* Good, because it would eliminate catastrophic backtracking structurally.
* Bad, because it requires a new runtime dependency, violating this project's zero-dependency architecture.

### Subprocess-per-match with a kill timeout

* Good, because it is platform-independent and enforces a true wall-clock timeout.
* Bad, because spawning a process per diff line is heavy overhead for what is meant to be a fast pre-commit/CI check.

### POSIX-only runtime timeout

* Good, because it is the simplest fix and slots directly into the existing `re.error` handling.
* Bad, because Windows CI is left with no protection at all -- a known, documented gap rather than a fix.

### Runtime timeout + static rejection (chosen)

* Good, because every supported platform gets at least one layer of defense.
* Bad, because the static heuristic only covers the nested-quantifier shape, not all ReDoS-prone patterns.

## Revisit Triggers

* A real ADR author needs a legitimate alternation-heavy pattern that the static check would need to distinguish from a ReDoS-prone one.
* Python gains a standard-library, cross-platform regex timeout mechanism, which would let the static heuristic be replaced by a strict runtime guard everywhere.
