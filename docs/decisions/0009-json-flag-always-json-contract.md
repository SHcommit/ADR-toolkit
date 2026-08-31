---
id: ADR-0009
title: --json is a documented no-op; CLI output is always JSON
status: accepted
date: 2026-08-30
locale: en
decision_makers:
  - YangSeungHyun
related: []
affected_paths:
  - skills/adr-toolkit/scripts/adr.py
  - README.md
  - skills/adr-toolkit/SKILL.md
  - tests/integration/test_cli.py
tags:
  - cli
  - output-contract
  - v0.2.0
retrospective: false
---

# --json is a documented no-op; CLI output is always JSON

## Context and Problem Statement

Every `adr.py` subcommand parsed a `--json` flag via argparse, but `main()` always printed `json.dumps(result, ...)` to stdout regardless of whether the flag was passed. The flag looked configurable in `--help` output but silently did nothing — a dead-flag bug that also left an unresolved question: should the tool grow a human-readable output mode, or should the flag be removed?

## Decision Drivers

* The tool's own code already carried a comment declaring a "JSON-only-stdout contract"; the flag contradicted that stated intent.
* Every real caller — every documented command in README/SKILL.md/quickstart, and every integration test — already passes `--json` explicitly. Only two SKILL.md steps and one README example omitted it.
* v0.2.0 is declared a non-breaking minor release; removing an accepted flag would be a breaking CLI change.
* Building a genuine human-readable mode means designing a format for fourteen different result shapes, an open-ended and unscoped effort not requested by any real usage.

## Considered Options

* Add a human-readable default output mode, with `--json` opting into the current JSON behavior (inverts today's actual default).
* Remove the `--json` flag entirely in a breaking CLI change.
* Keep current always-JSON behavior exactly as-is; formalize it as the deliberate, tested contract and document `--json` as an accepted no-op.

## Decision Outcome

Chosen option: **formalize always-JSON as the deliberate contract**, because it costs nothing — behavior does not change for a single existing caller — while resolving the standing ambiguity the dead flag created. This aligns with the tool's own "Deterministic Core" design: JSON is the one machine-readable contract agents and CI already rely on, and no request has ever surfaced a need for a second, human-readable output format.

The fourteen duplicated `--json` argument definitions were centralized into one `_add_json_flag()` helper with a `--help` string stating plainly that the flag has no effect and is kept only for backward compatibility. A regression test proves output is identical JSON whether or not `--json` is passed. The three documented call sites that had omitted the flag were updated to include it, for consistency rather than necessity.

### Consequences

* Good: the standing ambiguity is resolved without any behavior change or breaking release.
* Good: `--help` now tells the truth about what the flag does, instead of implying a choice that doesn't exist.
* Bad: `--json` remains a slightly confusing vestigial flag that a new contributor may still wonder about, even with the `--help` text.
* Bad: a genuine human-readable mode is deferred indefinitely rather than designed now, if a future use case (e.g. a human running the CLI directly, without an agent) ever wants one.

### Confirmation

* `tests/integration/test_cli.py::test_preflight_output_is_json_even_without_the_json_flag` asserts identical JSON output with and without `--json`.
* `python3 -m pytest -q` passes (327 tests) after the change.
* `python3 skills/adr-toolkit/scripts/adr.py preflight --help` shows the updated, accurate help text.

## Pros and Cons of the Options

### Add a human-readable default mode

* Good, because it would give `--json` genuine meaning again.
* Bad, because it inverts today's actual default behavior for the three call sites that currently omit the flag, and requires designing an unscoped, ad-hoc text format for fourteen different result shapes with no real usage evidence motivating it.

### Remove the flag entirely

* Good, because it eliminates the dead flag outright.
* Bad, because it is a breaking CLI change that would fail every existing documented and tested invocation, in a release explicitly declared non-breaking.

### Formalize always-JSON as the contract

* Good, because it changes zero behavior for zero existing callers while resolving the ambiguity.
* Bad, because the flag itself remains present and slightly confusing, rather than being cleanly resolved one way or the other.

## Revisit Triggers

* A real, evidenced need emerges for a human operator to run the CLI directly without an agent or script parsing its output.
* A future major/breaking release is already planned for unrelated reasons, making it a low-cost moment to drop the inert flag entirely.
