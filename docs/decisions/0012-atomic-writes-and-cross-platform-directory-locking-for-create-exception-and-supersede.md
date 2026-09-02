---
id: ADR-0012
title: Atomic writes and cross-platform directory locking for CREATE, EXCEPTION, and SUPERSEDE
status: accepted
date: 2026-09-01
locale: en
decision_makers:
  - YangSeungHyun
related:
  - ADR-0006
affected_paths:
  - skills/adr-toolkit/scripts/core/atomic_io.py
  - skills/adr-toolkit/scripts/commands/create.py
  - skills/adr-toolkit/scripts/commands/exception.py
  - skills/adr-toolkit/scripts/commands/supersede.py
  - tests/unit/test_atomic_io.py
tags:
  - concurrency
  - reliability
  - core
  - v0.3.0
retrospective: false
---

# Atomic writes and cross-platform directory locking for CREATE, EXCEPTION, and SUPERSEDE

## Context and Problem Statement

CREATE, EXCEPTION, and SUPERSEDE each compute the next sequential ID, check that no file with that ID exists yet, and write a new file with a direct `Path.write_text()` call. None of these three steps were protected by any lock or atomic operation. Reproducing the problem directly: 20 concurrent `create` invocations against the same repository produced only 13 unique ADR IDs, and 20 concurrent `exception` invocations produced only 18 unique IDs, before any fix. Separately, `write_text()` is not atomic -- a process killed mid-write (OOM kill, SIGKILL, power loss) can leave a torn, half-written file on disk.

## Decision Drivers

* This CLI has zero third-party runtime dependencies by design; the fix must use only the standard library.
* CI already runs the full test matrix on ubuntu, macOS, and Windows (Python 3.9-3.12), so any locking primitive must work identically on all three.
* Existing tests assert that a dry run creates nothing on disk (not even the ADR directory or a lock file); the fix must not break that guarantee.

## Considered Options

* Optimistic concurrency: write, then re-read to detect a collision, and retry
* Move ID allocation into an external state store (e.g. SQLite)
* Cross-platform advisory file locking (`fcntl` on POSIX, `msvcrt` on Windows) plus atomic temp-file-then-`os.replace()` writes

## Decision Outcome

Chosen option: **cross-platform advisory locking plus atomic writes**, because it solves both the ID-collision race and the torn-write problem using only the standard library, with no new runtime dependency and no change to the on-disk file format.

`core/atomic_io.py` provides `atomic_write_text()` (write to a temp file, `fsync`, then `os.replace()`) and `adr_directory_lock()` (a context manager using `fcntl.flock` on POSIX and `msvcrt.locking` on Windows). CREATE and EXCEPTION wrap ID allocation, the existence check, and the write inside the lock; their dry-run and (for EXCEPTION) schema-validation-failure paths stay outside the lock entirely, since those paths must not create the ADR directory or a lock file. SUPERSEDE wraps its full two-file update in the same lock and routes both writes, plus its rollback write, through `atomic_write_text()`.

### Consequences

* Good: concurrent `create`/`exception`/`supersede` invocations can no longer allocate duplicate IDs or corrupt each other's files.
* Good: a process killed mid-write never leaves a torn ADR or exception file -- verified at the OS level with a fork+SIGKILL test.
* Bad: SUPERSEDE's two-file update guarantees each individual file is atomic, but not that the *pair* stays consistent if the process is killed between the two writes; true two-phase commit across both files was explicitly scoped out.
* Bad: every successful CREATE/EXCEPTION/SUPERSEDE call leaves a `.adr-toolkit.lock` file permanently in the ADR/exceptions directory, as the cross-process mutex.

### Confirmation

`tests/unit/test_atomic_io.py` covers the primitives directly; the CREATE/EXCEPTION/SUPERSEDE test suites include a concurrency reproduction (20 parallel invocations must all get unique IDs) and assert dry-run/schema-error paths still create nothing on disk.

## Pros and Cons of the Options

### Optimistic concurrency (write, detect, retry)

* Good, because it needs no new locking primitive.
* Bad, because a correct retry loop is harder to get right than a lock, and it adds a new class of edge case (how many retries, what backoff) rather than removing one.

### External state store (SQLite)

* Good, because SQLite's own locking would handle the race correctly.
* Bad, because it introduces a new runtime dependency and a second source of truth alongside the Markdown/JSON files, conflicting with this project's zero-dependency, file-is-the-database design.

### Cross-platform advisory locking + atomic writes

* Good, because it uses only the standard library and fixes both the race and the torn-write problem in one primitive module.
* Bad, because POSIX and Windows locking semantics differ enough that the module needs two code paths, each tested separately.

## Revisit Triggers

* A future command needs true multi-file atomicity (e.g. an operation touching three or more files that must all succeed or all roll back together).
* Real-world usage shows the permanent `.adr-toolkit.lock` file causing confusion or tooling conflicts.
