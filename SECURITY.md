# Security Policy

## Supported Versions

Security fixes target the latest released version of ADR Toolkit.

## Reporting a Vulnerability

Please use GitHub's private vulnerability reporting form at
<https://github.com/SHcommit/ADR-toolkit/security/advisories/new> instead of
opening a public issue. Include:

- affected version or commit
- reproduction steps
- expected impact
- whether the issue affects generated ADR content, command execution, path
  handling, release automation, or plugin installation

Do not include exploit details in a public issue until a fix or mitigation is
available.

## Verifying a Release

Every `v*` release is built by `.github/workflows/release.yml` from a
tagged commit, and the workflow publishes a [GitHub Artifact
Attestation](https://docs.github.com/en/actions/security-guides/using-artifact-attestations-to-establish-provenance-for-builds)
for the packaged skill archive it attaches to the release
(`adr-toolkit-skill-vX.Y.Z.tar.gz`). This is a Sigstore-backed, keyless
signature -- no private key is held or rotated by this project -- proving
the archive was produced by this repository's own CI, from the exact
commit the release tag points to.

The repository has been public since 2026-08-29, so current releases are
eligible for attestation. The workflow keeps a private-repository guard only
so forks or future visibility changes fail safely; check a given release's
assets to confirm that its attestation was actually published.

To verify a downloaded archive:

```bash
# Checksum: confirms the file wasn't corrupted/tampered with in transit
sha256sum -c adr-toolkit-skill-vX.Y.Z.tar.gz.sha256

# Provenance: confirms the archive was actually built by this repo's CI,
# not a look-alike release from a compromised account or a different repo.
gh attestation verify adr-toolkit-skill-vX.Y.Z.tar.gz -R SHcommit/ADR-toolkit
```

Anyone consuming this repository directly (`git clone`, or an adapter's
`marketplace add`/`plugin add` pointing at the repo, which is how every
adapter installs this skill today) is verifying via Git/GitHub's own
commit and tag history rather than this archive -- the attestation is
primarily for the one path where a bare checkout doesn't happen: someone
who downloads the release archive off the GitHub Releases page directly.

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
