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

## Verifying a Release

Every `v*` release is built by `.github/workflows/release.yml` from a
tagged commit, and the workflow publishes a [GitHub Artifact
Attestation](https://docs.github.com/en/actions/security-guides/using-artifact-attestations-to-establish-provenance-for-builds)
for the packaged skill archive it attaches to the release
(`adr-toolkit-skill-vX.Y.Z.tar.gz`). This is a Sigstore-backed, keyless
signature -- no private key is held or rotated by this project -- proving
the archive was produced by this repository's own CI, from the exact
commit the release tag points to.

**While this repository is private, attestation is not generated** --
GitHub's attestation API rejects it for a user-owned private repository.
The release workflow skips that step automatically and still publishes
the archive and its checksum; attestation starts appearing on releases
once the repository goes public, with no workflow change required. Check
a given release's assets on the Releases page to see whether an
attestation is available for it.

To verify a downloaded archive:

```bash
# Checksum: confirms the file wasn't corrupted/tampered with in transit
sha256sum -c adr-toolkit-skill-vX.Y.Z.tar.gz.sha256

# Provenance: confirms the archive was actually built by this repo's CI,
# not a look-alike release from a compromised account or a different repo.
# Only available once this repository is public -- see the note above.
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
