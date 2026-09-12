# Accepted ADR Factual Correction Policy

This document defines the governance policy for making minor metadata and factual corrections to **`ACCEPTED`** Architecture Decision Records (ADRs) without invalidating their decision lifecycle or requiring a formal superseding process.

---

## 1. Overview & Core Philosophy

Architecture Decision Records (ADRs) are immutable historical logs of key architectural decisions. Once an ADR reaches the `ACCEPTED` state, its decision context, rationale, and consequences are considered settled.

However, non-substantive factual errors (such as typos, broken links, date formatting errors, or broken path references) occasionally require maintenance. This policy establishes a clear boundary between **Allowed Factual Corrections** (in-place edits) and **Decision Changes** (which require `adr supersede`).

---

## 2. Permitted Modifications (In-Place Edits Allowed)

The following minor changes may be made directly to an `ACCEPTED` ADR via a standard Pull Request:

1. **Typographical & Grammatical Fixes**: Correcting spelling errors, punctuation, or formatting issues that do not alter the technical meaning.
2. **Link & Path Updates**: Fixing broken URLs, updating repository file links, or updating relative documentation paths.
3. **Frontmatter Metadata Corrections**:
   - Fixing date format syntax errors (e.g. ISO 8601 formatting).
   - Correcting misspelled author names or contributor tags.
   - Updating non-semantic metadata fields (e.g. tags, categories).

---

## 3. Prohibited Modifications (Requires `adr supersede`)

The following changes **CANNOT** be made in-place to an `ACCEPTED` ADR:

1. **Modifying Technical Rationale or Context**: Altering the original trade-offs, problem statement, or decision context.
2. **Changing the Decision Outcome**: Reversing, modifying, or expanding the scope of an architectural decision.
3. **Altering Status Directly**: Changing `ACCEPTED` to `REJECTED` or `SUPERSEDED` by hand. Status transitions MUST use the `adr supersede` command to create a new successor ADR and maintain a verifiable audit trail.

---

## 4. Workflow & PR Conventions

When submitting an in-place factual correction for an `ACCEPTED` ADR:

1. **PR Title / Commit Prefix**: Use `docs(adr): [factual correction] <short description>`
2. **PR Description**: Explicitly state that the edit is a non-substantive factual correction under this policy.
3. **Review Requirement**: At least one standard maintainer review is required before merging.
