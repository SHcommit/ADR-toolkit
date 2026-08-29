---
id: ADR-0001
title: Use a provider port for LLM calls
status: accepted
date: 2026-08-01
decision_makers: []
related: []
affected_paths:
  - src/features/
tags:
  - architecture
retrospective: false
---

# Use a provider port for LLM calls

## Implementation Constraints

Feature modules must go through the LLM port; they must never import a
provider SDK directly.

```yaml
constraints:
  - id: no-provider-sdk-in-feature
    kind: forbidden_import
    paths: ["src/features/**"]
    pattern: ["openai", "anthropic"]
    severity: major
    message: "Feature modules must use the LLM port, not a provider SDK directly."
```
