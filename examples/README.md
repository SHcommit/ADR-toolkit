# ADR Toolkit Examples

This directory contains realistic, tested use-case walkthroughs demonstrating how to use ADR Toolkit in real projects.

> 🇰🇷 **한국어 문서**: 한국어 가이드는 [`ko/`](./ko/README.md) 디렉터리에서 확인하실 수 있습니다.

## Examples Overview

| Example | Focus / Use Case | Key Commands |
|---|---|---|
| [`basic-usage.md`](basic-usage.md) | **Basic Workflow**: Scaffolding a repository, checking significance, recording a decision, and generating a decision index. | `init`, `significance`, `create`, `index` |
| [`check-constraints.md`](check-constraints.md) | **Mechanical Constraint Enforcement**: Defining `forbidden_import` rules in ADRs, catching diff violations, refactoring, and registering exceptions. | `check`, `exception` |
| [`graph-visualization.md`](graph-visualization.md) | **Architecture Evolution & Graphs**: Marking superseded ADRs and exporting Mermaid (`.mmd`) / SVG (`.svg`) relationship dependency graphs. | `supersede`, `graph` |
| [`multilingual-adr.md`](multilingual-adr.md) | **Multilingual Repositories**: Using non-English titles/bodies (`--locale ko`) with approved ASCII filenames (`--slug`) and localized indices. | `init --locale`, `create --slug` |
| [`quickstart.md`](quickstart.md) | **Complete Walkthrough**: Step-by-step end-to-end tutorial covering setup to rule violation detection. | End-to-end sequence |

## Verification & Automation Pipeline

All CLI inputs and outputs in these examples are verified automatically against the core `adr.py` script. To run the verification suite or update example outputs after CLI logic changes:

```bash
# Run verification suite
python3 scripts/verify_examples.py --check

# Auto-update example outputs after CLI updates
python3 scripts/verify_examples.py --update
```

For real-world dogfooding, see [`../docs/decisions/`](../docs/decisions/) for the actual ADRs recording architectural decisions made while building ADR Toolkit itself.
