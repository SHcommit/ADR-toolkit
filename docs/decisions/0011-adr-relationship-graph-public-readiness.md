---
id: ADR-0011
title: Expose ADR relationships as Mermaid and SVG navigation artifacts
status: accepted
date: 2026-08-31
locale: en
decision_makers:
  - YangSeungHyun
related:
  - ADR-0001
  - ADR-0006
  - ADR-0008
  - ADR-0009
affected_paths:
  - README.md
  - CONTRIBUTING.md
  - SECURITY.md
  - .github/PULL_REQUEST_TEMPLATE.md
  - project-roadmap.md
  - docs/decisions/README.md
  - docs/decisions/relationships.mmd
  - docs/decisions/relationships.svg
  - skills/adr-toolkit/SKILL.md
  - skills/adr-toolkit/scripts/adr.py
  - skills/adr-toolkit/scripts/commands/graph.py
  - skills/adr-toolkit/scripts/commands/index.py
  - skills/adr-toolkit/scripts/core/relationships.py
  - tests/unit/test_graph_command.py
  - tests/unit/test_relationships.py
  - tests/unit/test_index.py
  - tests/unit/test_adr_cli.py
tags:
  - navigation
  - graph
  - documentation
  - governance
  - v0.2.0
retrospective: false
---

# Expose ADR relationships as Mermaid and SVG navigation artifacts

## Context and Problem Statement

ADR Toolkit intentionally keeps ADR source files flat under `docs/decisions/`, but a growing decision log still needs navigable relationship context. The generated index already listed supersession and related links as text, but users also wanted a graph view and a crisp image artifact. Raster screenshots were not acceptable because relationship graphs rely on small text and lines that become blurry when exported as PNG.

The same session also prepared the repository for public open-source use with contributor, security, and pull request guidance. That public surface should point contributors at the same deterministic ADR navigation and verification workflow rather than adding a separate documentation system.

## Decision Drivers

* Preserve the flat `docs/decisions/` storage model.
* Make relationship navigation visible in GitHub without requiring local tooling.
* Provide a sharp standalone image artifact for documents and reviews.
* Avoid making Node, Mermaid CLI, browser automation, or screenshot rendering required dependencies.
* Keep command output deterministic JSON and path handling consistent with the existing repository-scoped commands.
* Make public contribution guidance ask reviewers to consider ADR impact and verification.

## Considered Options

* Keep only the text relationship lists in the generated decision index.
* Embed Mermaid in the generated index and require Mermaid CLI or browser rendering for image export.
* Embed Mermaid in the generated index and generate standalone Mermaid plus Python-rendered SVG artifacts from the same relationship model.

## Decision Outcome

Chosen option: **embed Mermaid in the generated index and generate standalone Mermaid plus Python-rendered SVG artifacts**, because GitHub can render Mermaid directly while SVG gives a crisp vector artifact without adding external rendering dependencies.

`adr.py index` now appends a Mermaid `flowchart LR` block when `related` or `supersedes` edges exist. `adr.py graph --format mermaid|svg|both` exports `relationships.mmd` and/or `relationships.svg`; with `--format both`, a custom `--output` is treated as a prefix so one path can produce both extensions. Relative output paths resolve from `--root`, matching the other repository-scoped commands.

The public readiness docs added in the same decision are `CONTRIBUTING.md`, `SECURITY.md`, and `.github/PULL_REQUEST_TEMPLATE.md`. They make ADR impact, local verification, and security reporting explicit for future open-source contributors.

### Consequences

* Good: GitHub readers get an inline relationship graph without installing anything.
* Good: users who need an image get SVG, which remains sharp when zoomed or embedded in documents.
* Good: graph artifacts reuse the same deterministic relationship model as validation and index generation.
* Good: public contributors now see the expected branch, ADR, security, and verification workflow before opening a PR.
* Bad: the Python SVG renderer is a deliberately small navigation artifact, not a full Mermaid renderer or layout engine.
* Bad: generated `relationships.mmd` and `relationships.svg` are additional files that must be regenerated when ADR relationships change.

### Confirmation

* `tests/unit/test_relationships.py` covers Mermaid rendering, label escaping, no-edge behavior, and SVG output.
* `tests/unit/test_graph_command.py` covers default export, custom output prefix behavior for `--format both`, and `--root`-relative output paths.
* `tests/unit/test_index.py` covers Mermaid graph insertion in the generated decision index.
* `tests/unit/test_adr_cli.py` covers parser registration for `adr.py graph`.
* `python3 -m pytest -q` passes with 395 tests.
* `python3 scripts/sync_version.py --check`, `adr.py validate`, `adr.py index`, and `adr.py graph --format both` all pass.

## Implementation Constraints

```yaml
constraints:
  - id: graph-export-no-external-renderer
    kind: forbidden_import
    paths: ["skills/adr-toolkit/scripts/commands/graph.py", "skills/adr-toolkit/scripts/core/relationships.py"]
    pattern: ["^\\s*import\\s+subprocess\\b", "^\\s*from\\s+subprocess\\b", "^\\s*import\\s+playwright\\b", "^\\s*from\\s+playwright\\b", "^\\s*import\\s+selenium\\b", "^\\s*from\\s+selenium\\b"]
    severity: major
    message: "ADR graph export must stay deterministic and must not require external renderers or browser automation."
```

## Pros and Cons of the Options

### Keep only text relationship lists

* Good, because it requires no new command or generated artifact.
* Bad, because relationship navigation remains harder to scan as ADR count grows, and users still lack a sharp visual artifact.

### Mermaid plus external renderer

* Good, because Mermaid CLI can produce familiar graph output.
* Bad, because requiring Node, browser automation, or screenshot rendering expands the dependency surface and reintroduces blurry PNG output unless users tune scale settings.

### Mermaid plus Python-rendered SVG

* Good, because the README stays GitHub-native and the standalone image remains vector-sharp.
* Good, because it keeps graph export inside the existing deterministic Python package.
* Bad, because the SVG layout is intentionally simple and may need a richer layout strategy if real ADR graphs become dense.

## Revisit Triggers

* Real repositories produce dense relationship graphs that the simple SVG layout cannot make readable.
* Users need a PNG export despite SVG availability, and can define acceptable scale/DPI behavior.
* Mermaid syntax compatibility changes on GitHub and breaks the embedded graph.
* Multiple repositories need a combined cross-repository graph rather than one graph per ADR directory.
