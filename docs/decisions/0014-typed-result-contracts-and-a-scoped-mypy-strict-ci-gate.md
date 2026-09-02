---
id: ADR-0014
title: Typed result contracts and a scoped mypy --strict CI gate
status: accepted
date: 2026-09-01
locale: en
decision_makers:
  - YangSeungHyun
related:
  - ADR-0009
affected_paths:
  - skills/adr-toolkit/scripts/core/contracts.py
  - .github/workflows/test.yml
  - tests/unit/test_contracts.py
tags:
  - typing
  - contract
  - core
  - v0.3.0
retrospective: false
---

# Typed result contracts and a scoped mypy --strict CI gate

## Context and Problem Statement

Every one of the 16 commands returns a plain `dict` as its stdout JSON result, per this project's fixed "stdout is always JSON" contract. But that JSON's actual shape existed only in each command's `run()` function body -- there was no type-level definition of what keys a caller (an agent, a CI script) could rely on. A typo'd or dropped field would only surface at runtime, in whichever consumer happened to read it.

## Decision Drivers

* No third-party runtime dependency may be introduced (rules out `jsonschema`-based runtime validation).
* The fix should not change runtime behavior -- only make the existing contract checkable statically.
* `argparse.Namespace`-based command arguments resist `TypedDict` typing without a larger `Protocol`-based refactor; that refactor is out of scope for this pass.

## Considered Options

* Add `jsonschema` and validate every command's output against a JSON Schema at runtime
* Wrap every result in a `dataclass` and serialize with `asdict()`
* Define `TypedDict` result shapes in a new `core/contracts.py` and gate them with `mypy --strict`, scoped to already-fully-typed modules

## Decision Outcome

Chosen option: **`TypedDict` contracts plus a scoped `mypy --strict` gate**, because `TypedDict` has zero runtime cost, requires no new dependency, and lets the type checker -- rather than a runtime validator -- catch a shape mismatch before it ships.

`core/contracts.py` defines one `TypedDict` per command's result shape, covering all 16 commands. A `type-check` CI job runs `mypy --strict` over the modules that are fully type-annotated (`atomic_io`, `telemetry`, `contracts`); extending strict mode into the 16 command modules themselves is deferred until their `argparse.Namespace` arguments are typed. Each `TypedDict`'s fields were read directly from the corresponding command's actual `return` statements -- including at least one error-path branch for `status` and `supersede` -- rather than inferred from documentation. Where a command's real error or warning payload carries fields the shared `CommandError` type doesn't declare (e.g. `file`, `id`, `ids`, `cycle`), that field is typed `Dict[str, Any]` instead of `CommandError`, so the contract never claims more structure than the code actually guarantees.

### Consequences

* Good: the output contract for all 16 commands is now expressed in code and checked by `mypy --strict` in CI, not just implied by convention.
* Good: adding this caught 3 real, pre-existing type errors in `atomic_io.py`/`telemetry.py` (a missing generator return type, an unnarrowed `Optional` access, and an unparameterized generic).
* Bad: command *argument* types (`argparse.Namespace`) remain untyped, so `mypy --strict` does not yet cover a command's full implementation, only its result shape.

### Confirmation

`tests/unit/test_contracts.py` asserts that each command's actual JSON output is a valid subset of its declared `TypedDict` keys; `.github/workflows/test.yml`'s `type-check` job runs `mypy --strict` on every push and pull request.

## Pros and Cons of the Options

### `jsonschema` runtime validation

* Good, because JSON Schema is a widely understood, tool-agnostic format.
* Bad, because it adds a runtime dependency to a project that deliberately has none, and validates on every call instead of at development time.

### `dataclass` + `asdict()`

* Good, because it gives real runtime objects, not just static types.
* Bad, because it requires rewriting all 16 commands and their tests to build and return dataclass instances instead of dicts -- a much larger change than the contract gap actually calls for.

### `TypedDict` + scoped `mypy --strict` (chosen)

* Good, because it adds a type-level contract with no runtime cost and no new dependency.
* Bad, because `TypedDict` provides no runtime enforcement -- a command could still, in principle, return a dict that mypy didn't check if the command module itself stays outside strict mode.

## Revisit Triggers

* `argparse.Namespace` gets a `Protocol`-based typed wrapper, at which point `mypy --strict` coverage should extend into the 16 command modules themselves.
* A consumer reports a real production bug caused by a result-shape mismatch that `TypedDict` alone did not prevent, which would argue for adding runtime validation after all.
