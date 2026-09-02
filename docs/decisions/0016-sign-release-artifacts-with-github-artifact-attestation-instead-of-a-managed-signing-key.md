---
id: ADR-0016
title: Sign release artifacts with GitHub Artifact Attestation instead of a managed signing key
status: accepted
date: 2026-09-01
locale: en
decision_makers:
  - YangSeungHyun
related:
  - ADR-0005
  - ADR-0011
affected_paths:
  - .github/workflows/release.yml
  - SECURITY.md
tags:
  - release
  - security
  - supply-chain
  - v0.3.0
retrospective: false
---

# Sign release artifacts with GitHub Artifact Attestation instead of a managed signing key

## Context and Problem Statement

`.github/workflows/release.yml` ran tests, checked manifest version sync, verified the pushed tag matched `VERSION`, and published a GitHub Release -- but the release carried no checksummed or signed artifact of any kind. Unlike a typical npm/PyPI project, this toolkit has no separately-built distributable: every install path (Claude Code's `marketplace.json` with `source: "./"`, Codex/Gemini CLI plugin installs, a plain `git clone`) consumes the git repository or the `skills/adr-toolkit/` folder directly. That meant the usual "checksum and sign the build artifact" pattern had no artifact to attach to in the first place.

## Decision Drivers

* This project's own release process (documented in `AGENTS.md`) has a human create and push the version tag locally -- CI only ever sees an already-pushed tag, so it cannot retroactively sign the tag itself.
* No private signing key should need to be generated, stored, or rotated by a single-maintainer project.
* Whatever gets signed should matter to at least one real consumption path, not be signed purely for form's sake.

## Considered Options

* Sign the git tag itself with GPG
* Package a tarball and only checksum it (no provenance signature)
* Package a tarball, checksum it, and generate a GitHub Artifact Attestation (Sigstore-backed, keyless)
* Manage a project GPG key as a repository secret and sign a packaged artifact with it

## Decision Outcome

Chosen option: **package plus checksum plus GitHub Artifact Attestation**, because it is the only option that provides real provenance (not just transit-integrity) for the one consumption path that doesn't already trust Git/GitHub's own commit history -- someone downloading the release archive directly from the GitHub Releases page -- without requiring any private key management.

`release.yml` now packages `skills/adr-toolkit/` into `adr-toolkit-skill-v${VERSION}.tar.gz`, computes its SHA-256 checksum, and runs `actions/attest-build-provenance@v2` against it, using the workflow's OIDC token to produce a Sigstore-backed, keyless attestation. Both the archive and its checksum are attached to the GitHub Release. `SECURITY.md` documents `sha256sum -c` and `gh attestation verify` as the two verification steps, and states explicitly that `git clone`/adapter-install paths verify through Git/GitHub's own commit and tag history instead, since they never touch this archive.

### Consequences

* Good: anyone who downloads the release archive directly can cryptographically verify it was built by this repository's own CI from the exact tagged commit, with no key for the maintainer to generate or protect.
* Good: adding this required no change to the existing tag-then-push release trigger.
* Bad: the attestation only covers the one archive-download path; every adapter-based install path (the majority of actual installs today) is unaffected by this change and continues to rely on Git/GitHub history alone.

### Confirmation

`release.yml`'s YAML was validated for syntax; the packaging and checksum steps' shell logic were reviewed locally. The OIDC-based attestation issuance and `gh attestation verify` round trip can only be fully confirmed against a real `v*` tag push, since GitHub's attestation API is not available to a local dry run.

## Pros and Cons of the Options

### GPG-sign the git tag

* Good, because a signed tag is a widely recognized supply-chain practice.
* Bad, because this project's tags are created locally by a human before the push that triggers CI -- CI never has an opportunity to sign the tag itself, only whatever it produces after the fact.

### Checksum only, no signature

* Good, because it is the simplest possible improvement and needs no new CI permissions.
* Bad, because a checksum only proves the file wasn't corrupted in transit; it says nothing about who produced it, so it cannot detect a look-alike release from a compromised account.

### Package + checksum + GitHub Artifact Attestation (chosen)

* Good, because it adds real provenance with no private key to manage, using GitHub's own OIDC/Sigstore integration.
* Bad, because it only protects the archive-download path, not the more common adapter-install paths.

### Repository-secret GPG key

* Good, because GPG signatures are recognized by tools outside GitHub's own ecosystem.
* Bad, because a single-maintainer project would then be responsible for key generation, secure storage, and rotation -- operational burden with no corresponding increase in trust over the keyless option.

## Revisit Triggers

* This project starts publishing to a package registry (npm, PyPI) with its own signing conventions, which would need its own decision.
* A consumer outside the GitHub ecosystem needs to verify a release without `gh` or without trusting Sigstore's transparency log.
