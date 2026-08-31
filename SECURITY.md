# Security Policy

## Supported Versions

Security fixes target the latest released version of ADR Toolkit.

## Reporting a Vulnerability

Please report security issues privately to the repository owner before opening a
public issue. Include:

- affected version or commit
- reproduction steps
- expected impact
- whether the issue affects generated ADR content, command execution, path
  handling, release automation, or plugin installation

Do not include exploit details in a public issue until a fix or mitigation is
available.

## Scope

In scope:

- command injection or unsafe path handling in deterministic scripts
- release workflow or version provenance problems
- plugin manifest behavior that can install or expose unintended files
- validation bugs that silently report clean results for invalid ADR state

Out of scope:

- disagreement with an ADR's architectural recommendation
- AI-generated prose quality
- unsupported third-party harness behavior outside this repository's adapters
