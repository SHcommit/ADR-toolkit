# Public Readiness and ADR Graph Design

## Scope

Prepare ADR Toolkit for public open-source use and add a sharper ADR navigation
view without changing the canonical flat `docs/decisions/` storage model.

## Decisions

- Keep ADR Markdown files flat in `docs/decisions/`.
- Add a Mermaid relationship graph to the generated decision index so GitHub can
  render it directly.
- Add a deterministic `adr.py graph` export command that writes
  `relationships.mmd` and, when requested, a vector `relationships.svg`.
- Generate SVG directly from the same relationship model in Python. The SVG is a
  navigation artifact, not a pixel screenshot, so it remains crisp when zoomed.
- Keep PNG out of the default workflow. Raster export can be revisited later if
  users explicitly need it.
- Add public repository hygiene docs: contributing guidance, security reporting,
  and a pull request template.

## Validation

- Unit tests must cover Mermaid block rendering, Mermaid file export, SVG file
  export, and graph behavior when no relationships exist.
- Existing ADR validation, index generation, version drift, and full pytest must
  pass before completion.
