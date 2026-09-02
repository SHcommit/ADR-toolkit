---
id: ADR-0015
title: Structured JSON stderr logging with correlation IDs for uncaught errors
status: accepted
date: 2026-09-01
locale: en
decision_makers:
  - YangSeungHyun
related:
  - ADR-0009
affected_paths:
  - skills/adr-toolkit/scripts/core/telemetry.py
  - skills/adr-toolkit/scripts/adr.py
  - tests/unit/test_telemetry.py
tags:
  - observability
  - core
  - v0.3.0
retrospective: false
---

# Structured JSON stderr logging with correlation IDs for uncaught errors

## Context and Problem Statement

When an uncaught exception reached `adr.py`'s top-level handler, it was converted into a JSON error response on stdout, but the exception's context and stack trace were discarded -- nothing was recorded anywhere else. A CI pipeline or agent harness that hit a failure had no way to look up what actually happened, and no way to tie a given stdout failure back to any diagnostic detail.

## Decision Drivers

* stdout must remain pure, contract-stable JSON (established by ADR-0009); diagnostic output cannot be mixed into it.
* Multiple `adr.py` invocations can run concurrently in CI; an unstructured stderr line has no way to be matched back to the specific stdout response it belongs to.
* The test suite uses pytest's `capsys` to capture stderr; a logging setup that accumulates handlers across calls breaks that capture between tests.
* No new runtime dependency (e.g. a hosted logging service) may be introduced.

## Considered Options

* Send errors to an external logging service (e.g. Sentry)
* Print unstructured tracebacks to stderr
* Standard-library `logging`, emitting JSON Lines to stderr, with a correlation ID shared between the stderr log line and the stdout JSON error response

## Decision Outcome

Chosen option: **structured JSON Lines on stderr with a shared correlation ID**, because it needs no new dependency or network call, and the correlation ID lets a CI log or agent harness join a specific stdout failure to its stderr diagnostic detail.

`core/telemetry.get_logger(operation)` returns a `LoggerAdapter` that emits JSON Lines to stderr with `level`, `operation`, `correlation_id`, `message`, and (on exceptions) `exception_type`. `adr.py`'s global exception handler logs through this adapter and includes the same `correlation_id` in the stdout JSON error response. The default log level is `WARNING` (silent on success); `ADR_TOOLKIT_LOG_LEVEL` overrides it. Critically, `get_logger()` clears and rebuilds its logger's handlers on every call, rather than accumulating them -- this is what keeps pytest's per-test `capsys` capture correct and prevents unbounded handler growth in a long-running process.

### Consequences

* Good: a CI failure's stdout JSON response and its stderr diagnostic log line can now be matched by `correlation_id`.
* Good: stdout's JSON-only contract is unchanged except for the additive `correlation_id` field.
* Bad: logs go only to local stderr -- there is no built-in shipping to a centralized log store; that remains the consuming CI/harness's responsibility.

### Confirmation

`tests/unit/test_telemetry.py` verifies the JSON Lines shape and that repeated `get_logger()` calls don't accumulate handlers; `tests/unit/test_adr_cli.py` verifies the stdout error response's `correlation_id` matches what was logged.

## Pros and Cons of the Options

### External logging service

* Good, because it would give centralized, queryable log storage out of the box.
* Bad, because it requires network access and credential management, which conflicts with this CLI's install-and-run-immediately model and its zero-dependency principle.

### Unstructured stderr tracebacks

* Good, because it is the simplest possible change.
* Bad, because concurrent CI runs interleave their stderr output with no way to tell which traceback belongs to which invocation or which stdout response.

### Structured JSON Lines + correlation ID (chosen)

* Good, because it solves the matching problem with only the standard library.
* Bad, because it is still a local-only log -- aggregating logs across many CI runs still requires the harness to collect and store stderr itself.

## Revisit Triggers

* A harness or CI setup needs logs shipped somewhere other than local stderr, which would require revisiting the zero-dependency stance for this specific concern.
* `ADR_TOOLKIT_LOG_LEVEL` proves insufficient and per-operation log-level configuration is needed.
