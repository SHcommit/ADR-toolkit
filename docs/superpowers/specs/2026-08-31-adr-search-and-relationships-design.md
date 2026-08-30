# ADR Search and Relationship Navigation Design

## Context and Problem

ADR Toolkit ships as an open-source, multi-harness skill meant for other developers and
teams to adopt, not just for this repository's own 10 ADRs. `project-roadmap.md`'s "ADR
navigation and scale" item flagged this as future work, gated on evidence. Research into
comparable real-world tools (`npryce/adr-tools`, the classic flat-file CLI with no search;
`thomvaill/log4brains`, 1.5k GitHub stars, the most-adopted actively maintained ADR tool)
shows the two features that actually matter for any team running an ADR practice over time
are **search** and **relationship visibility** — not folder restructuring, not semantic
search, not a web UI. Those two are proven table-stakes for any team, regardless of current
repository size; building them now is not premature relative to real adopters, even though
this repository itself only has 10 ADRs today.

Two concrete gaps exist today:

1. `related.py` — the only existing lookup command — matches a keyword against `title`
   only, never `body`. A decision phrase that lives in the rationale/context, not the
   title, cannot be found.
2. The generated `docs/decisions/README.md` shows *that* an ADR is `superseded` (under "By
   status") but never shows *what superseded it* without opening the file. `related`/
   `supersedes` links are invisible from the index.

## Goals

- Let a human or an agent find an existing ADR by keyword (title **and** body), tag, or
  status, without opening every file.
- Make supersession and relatedness visible directly in the generated index.
- Fix `related`'s title-only keyword gap as part of the same change, since it's the same
  underlying defect.
- Keep the CLI/agent-native shape this project already has: no web server, no static site,
  no new storage format.

## Non-goals (stay in `project-roadmap.md`, unchanged)

- Rendered graph images / DOT / Mermaid visualization of relationships.
- Full-text indexing, ranking, or semantic/vector search.
- Directory sharding or an alternate storage layout.

These remain explicitly deferred until real usage (per the roadmap's own stated
threshold) demonstrates substring/tag/status matching and a text-based relationship list
are insufficient.

## Components

### 1. `scripts/core/search.py` — shared matching primitives

New module, reused by both `related` and the new `search` command:

```python
def matches_keyword(keyword: str, title: str, body: str) -> bool
def matches_tags(query_tags: set, entry_tags: list) -> set  # returns the overlap
def matches_paths(query_paths: set, affected_paths: list) -> set  # returns the overlap
```

`matches_keyword` is the fix: case-insensitive substring match against `title` **or**
`body`, not title alone. `matches_tags`/`matches_paths` extract `related.py`'s existing
set-intersection logic unchanged, so `related.py` becomes a thin caller of this module
instead of owning duplicate logic.

### 2. `related.py` — fixed, not replaced

Update its keyword check to call `search.matches_keyword(keyword, title, body)` instead of
`keyword in data.get("title", "").lower()`. No interface change — same command, same
output shape, same DISCOVER-stage purpose (finding conflicts/precedent for a *new* draft
under RECORD). A regression test proves a body-only match now succeeds.

### 3. `scripts/commands/search.py` — new command

```
adr.py search [--keyword TEXT] [--tag TAG ...] [--status STATUS] --dir docs/decisions --json
```

Distinct from `related` in purpose and default behavior: `search` is for ad-hoc lookup
(by a human at a terminal, or an agent answering "have we decided this before?"), not tied
to drafting a new ADR. With **no filters given, it returns every non-skip ADR** (browse
mode) — the opposite of `related`'s current "no filters -> no matches" behavior, which is
correct for *its* purpose (nothing to relate to) but wrong for a general search command
(an empty query should list, not return nothing).

Result shape:

```json
{
  "ok": true,
  "operation": "search",
  "count": 2,
  "results": [
    {
      "id": "ADR-0007",
      "filename": "0007-check-confidence-field.md",
      "title": "Promote CHECK's kind-to-confidence mapping to a stable output field",
      "status": "accepted",
      "tags": ["check", "confidence", "v0.2.0"],
      "matched_in": ["title", "tags"]
    }
  ],
  "warnings": []
}
```

`matched_in` lists which field(s) caused the match (`title`, `body`, `tags`, `status`),
kept for the same transparency reason CHECK findings carry `reasons` — a consumer should
never have to trust a match blindly.

Uses `core.adr_directory.iter_adr_files` for the walk and `frontmatter.parse` for
frontmatter, matching every other command's pattern. A malformed ADR degrades to a
`BAD_FRONTMATTER` warning, same as `related`/`check`/`validate`.

### 4. `index.py` — Relationships section

New generated section, after "Chronological", localized like every other section header:

```
## Relationships

### Supersession chains
- ADR-0003 → superseded by → ADR-0006

### Related
- ADR-0007 related to: ADR-0002
```

Only ADRs that actually carry a `supersedes`/`superseded_by`/non-empty `related` are
listed — an ADR with none of those is omitted from this section entirely (no noise).
`entries` in `run()` gains `related`, `supersedes`, `superseded_by` from frontmatter
(currently not collected).

New i18n keys (`relationships`, `supersession_chains`, `related`, `superseded_by`,
`related_to`), added to `FALLBACK_STRINGS` and all 8 locale catalogs
(`skills/adr-toolkit/scripts/i18n/{en,ko,ja,zh,fr,es,de,pt-BR}.json`), following the exact
pattern `by_status`/`by_tag` already established.

## Testing

- `tests/unit/test_search_module.py` — `matches_keyword`/`matches_tags`/`matches_paths` in
  isolation.
- `tests/unit/test_search_command.py` — keyword-in-title, keyword-in-body, tag filter,
  status filter, no-filter-returns-all, `matched_in` correctness, malformed-ADR warning.
- `tests/unit/test_related.py` — new regression test: keyword present only in body now
  matches.
- `tests/unit/test_index.py` — Relationships section renders a supersession chain and a
  related list; an ADR with no relationships is absent from the section.
- `tests/unit/test_locale.py` — extended to cover the five new keys in the existing
  8-catalog exact-key-set parity check.
- `tests/integration/test_localized_workflow.py` or equivalent — `search` and the new
  index section produce valid output in at least one non-English locale.

## Documentation

- `README.md` — add `search` alongside the existing `related`/`check` usage examples.
- `skills/adr-toolkit/SKILL.md` — document when an agent should reach for `search` versus
  `related` (ad-hoc lookup vs. DISCOVER-stage conflict check).
- Run every newly documented command in a scratch repository before treating the docs as
  accurate, matching this project's existing practice.

## Open question for implementation

None outstanding — scope, interfaces, and file list above are considered final for this
spec. `writing-plans` should sequence: (1) `core/search.py` + its tests, (2) `related.py`
fix + regression test, (3) `search` command + tests + CLI wiring, (4) `index.py`
Relationships section + 8-locale catalog updates + tests, (5) docs, (6) full suite +
`sync_version.py --check` + a real scratch-repo run of every new documented command.
