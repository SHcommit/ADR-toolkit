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

Guiding principle for this design: **keep ADR storage boring; make ADR retrieval
powerful.** Storage stays flat Markdown + frontmatter + Git — nothing here changes that.
Retrieval gets a real, shared, deterministic core that both a human at a terminal and an
agent consume identically.

Three concrete gaps exist today:

1. `related.py` — the only existing lookup command — matches a keyword against `title`
   only, never `body`. A decision phrase that lives in the rationale/context, not the
   title, cannot be found.
2. The generated `docs/decisions/README.md` shows *that* an ADR is `superseded` (under "By
   status") but never shows *what superseded it*, and never shows `related` links at all,
   without opening the file.
3. `validate.py` checks that `related` IDs point at real ADRs (`BROKEN_RELATED_LINK`), but
   `supersedes`/`superseded_by` are never checked for existing or mutually consistent —
   `adr.py supersede` writes both sides atomically today, but nothing catches it if a
   frontmatter field is later hand-edited into an inconsistent state.

## Goals

- Let a human or an agent find an existing ADR by keyword (title **and** body), tag,
  status, or the file path it governs — without opening every file.
- Return results in a deterministic, best-match-first order.
- Keep result size and shape safe for an agent's context window (`--limit`, `total`,
  `truncated`).
- Make supersession and relatedness visible directly in the generated index, by title not
  just ID.
- Catch broken or inconsistent relationship metadata as a structural validation error, the
  same way a broken `related` link already is.
- Fix `related`'s title-only keyword gap as part of the same change, since it's the same
  underlying defect — without changing its existing matching *policy*.
- Keep the CLI/agent-native shape this project already has: no web server, no static site,
  no new storage format, no ranking model beyond simple deterministic tiers.

## Non-goals (stay in `project-roadmap.md`, unchanged)

- Rendered graph images / DOT / Mermaid visualization of relationships.
- Full-text indexing, ranking algorithms (BM25/TF-IDF), or semantic/vector search.
- Relationship cycle detection (the model below doesn't block adding it later; it's simply
  not built now — no cycle has ever occurred in this repository's 10 ADRs).
- Directory sharding or an alternate storage layout.
- A standalone `adr.py relationships <id>` command or `--id` exact lookup — small,
  plausible near-future additions, deliberately left out of this spec to keep it focused.

These remain explicitly deferred until real usage (per the roadmap's own stated
threshold) demonstrates the deterministic, substring-based approach here is insufficient.

## Components

### 1. `scripts/core/query.py` — shared matching and ranking primitives

```python
def matches_keyword(keyword: str, title: str, body: str) -> bool
def matches_tags_any(query_tags: set, entry_tags: list) -> set       # overlap, used by related's OR policy
def matches_paths_exact(query_paths: set, affected_paths: list) -> set  # overlap, used by related's OR policy
def path_governed_by(path: str, affected_paths: list) -> bool        # prefix/glob overlap, used by search --path
def rank_key(entry: dict, keyword: str) -> tuple                     # deterministic best-match-first sort key
```

`matches_keyword` is the bug fix: case-insensitive substring match against `title` **or**
`body`, not title alone.

`matches_tags_any`/`matches_paths_exact` are `related.py`'s existing set-intersection logic,
extracted unchanged — this is the matching policy a broad, "cast a wide net before
drafting" discovery command wants.

`path_governed_by` is a **different, new** matching policy: does a single real file path
fall under any of an ADR's `affected_paths`, using the same directory-boundary prefix and
glob logic `scripts/rules/conflict.py`'s `affected_paths_overlap`/`_path_under` already use
for CHECK. This is deliberately not the same function as `matches_paths_exact` — "does this
ADR's frontmatter literally list this path" (what `related` needs when comparing a new
draft's exact `affected_paths`) and "does this real file fall under an ADR's governed
scope" (what `search --path` needs when an agent asks "does anything govern
`src/payment/x.py`?") are genuinely different questions.

Layering note: `rules/conflict.py` already imports `core/globs.py` (nothing in `core/`
currently imports from `rules/`, and this spec doesn't introduce that direction). So
`_path_under` moves *into* `core/globs.py` as a new public `globs.path_under(path, prefix)`
— `conflict.py` is refactored to call it instead of owning a private copy, and
`query.path_governed_by` calls the same function. One implementation, no new dependency
direction between `core` and `rules`.

`rank_key` orders results deterministically, best match first, using fixed tiers (highest to
lowest): exact ID match, exact title match, title substring match, tag exact match, body
substring match. No numeric score is exposed in the JSON output — the tiering is an
internal sort key, not a stable public contract, avoiding over-committing to arbitrary
weights.

### 2. `scripts/core/relationships.py` — canonical relationship model

```python
class Relationship(NamedTuple):
    source: str   # ADR id
    type: str     # "related" | "supersedes" | "superseded_by"
    target: str

def resolve(entries: list) -> list[Relationship]
def missing_targets(relationships: list, known_ids: set) -> list[Relationship]
def supersession_mismatches(relationships: list) -> list[tuple]  # (supersedes_edge, expected_but_missing_or_wrong)
```

`resolve()` turns each ADR's `related`/`supersedes`/`superseded_by` frontmatter into a flat
list of edges. `index.py`, `validate.py`, and any future consumer (a graph renderer, an MCP
tool) read this same list instead of each re-deriving relationship data from raw frontmatter
independently — this is the one piece of real structural investment in this spec, and it's
what keeps `index.py`'s section from becoming ad-hoc string-building that a future feature
would have to reverse-engineer.

### 3. `related.py` — fixed, not replaced, policy unchanged

Updated to import `matches_keyword`, `matches_tags_any`, `matches_paths_exact` from
`core/query.py` instead of owning duplicate logic. Keyword now matches body too (the fix).
**Combination policy is unchanged**: a path OR a tag OR a keyword match is enough to
include an ADR ("related" wants a broad net before drafting) — this is `related`'s existing,
tested behavior and this spec does not change it. A regression test proves a body-only
keyword match now succeeds; all thirteen existing `related` tests must keep passing
unmodified.

### 4. `scripts/commands/search.py` — new command

```
adr.py search [--keyword TEXT] [--tags TAG [TAG ...]] [--status STATUS] [--path PATH]
              [--limit N] --dir docs/decisions --json
```

`--tags` matches `related.py`'s existing flag name and `nargs="*"` shape for CLI
consistency (space-separated values under one flag, not a repeatable `--tag`).

Distinct purpose from `related`: general lookup ("what ADRs exist?"), not tied to drafting.
Two policy differences from `related`, both deliberate:

- **Filters across different fields combine with AND; multiple values within the same
  field combine with OR.** `--keyword database --tags postgres mysql --status
  accepted` means: keyword matches AND (tag is postgres OR mysql) AND status is accepted.
  This must be documented explicitly in `--help` and the README — an agent must never have
  to guess implicit CLI semantics.
- **No filters given returns every non-skip ADR** (browse mode), the opposite of
  `related`'s "no filters -> no matches." An empty query on a lookup command should list,
  not return nothing.

`--path` uses `query.path_governed_by`, matching CHECK's real-file-vs-governed-scope
semantics, not `related`'s exact frontmatter-list semantics.

Result shape:

```json
{
  "ok": true,
  "operation": "search",
  "query": {"keyword": "confidence", "tags": ["check"], "status": null, "path": null, "limit": null},
  "count": 2,
  "total": 2,
  "truncated": false,
  "results": [
    {
      "id": "ADR-0007",
      "filename": "0007-check-confidence-field.md",
      "path": "docs/decisions/0007-check-confidence-field.md",
      "title": "Promote CHECK's kind-to-confidence mapping to a stable output field",
      "status": "accepted",
      "tags": ["check", "confidence", "v0.2.0"],
      "matched_in": ["title", "tags"]
    }
  ],
  "warnings": []
}
```

`matched_in` lists which field(s) caused the match (`title`, `body`, `tags`, `status`,
`path`) — kept exactly as originally designed, for the same transparency reason CHECK
findings carry `reasons`: a consumer should never have to trust a match blindly. Detailed
per-field match evidence (e.g. which substring matched) is deferred — `matched_in` alone is
enough for MVP.

`--limit N` truncates `results` to N entries (already rank-ordered, so truncation drops the
weakest matches, not arbitrary ones); `total` is always the untruncated match count;
`truncated` is `true` iff `total > count`. No default limit — unlimited unless requested,
matching every other command's current behavior; the fields exist so a harness *can* bound
its own consumption, not so the tool imposes one.

Uses `core.adr_directory.iter_adr_files` for the walk and `frontmatter.parse` for
frontmatter, matching every other command's pattern. A malformed ADR degrades to a
`BAD_FRONTMATTER` warning, same as `related`/`check`/`validate`.

### 5. `index.py` — Relationships section

New generated section, after "Chronological", built from `relationships.resolve()` instead
of ad-hoc string building, localized like every other section header:

```
## Relationships

### Supersession chains
- ADR-0003 "Localize only index.py's generated strings..." → superseded by → ADR-0006 "Localize deterministic ADR generation..."

### Related
- ADR-0007 "Promote CHECK's kind-to-confidence..." related to: ADR-0002 "Limit CHECK's conflict detection..."
```

Titles are shown alongside IDs (not IDs alone) — a developer reading the generated README
should understand a relationship without opening either file. Only ADRs that actually carry
a `supersedes`/`superseded_by`/non-empty `related` are listed; an ADR with none of those is
omitted entirely (no noise). `entries` in `run()` gains `related`, `supersedes`,
`superseded_by` from frontmatter (currently not collected).

New i18n keys (`relationships`, `supersession_chains`, `related`, `superseded_by`,
`related_to`), added to `FALLBACK_STRINGS` and all 8 locale catalogs
(`skills/adr-toolkit/scripts/i18n/{en,ko,ja,zh,fr,es,de,pt-BR}.json`), following the exact
pattern `by_status`/`by_tag` already established.

### 6. `validate.py` — relationship integrity

Extends the existing `known_ids`/`BROKEN_RELATED_LINK` check (which today only covers
`related`) using `relationships.resolve()` and `relationships.missing_targets()`/
`supersession_mismatches()`:

- `BROKEN_SUPERSESSION_LINK` — a `supersedes` or `superseded_by` value references an ADR ID
  that doesn't exist among `known_ids`. Same severity and shape as the existing
  `BROKEN_RELATED_LINK`.
- `SUPERSESSION_MISMATCH` — ADR A's `supersedes` lists B, but B's `superseded_by` isn't A
  (missing or pointing elsewhere). Catches exactly the case `adr.py supersede` normally
  prevents by writing both sides atomically, but a hand-edit could still produce.

Both are **errors**, not warnings — `validate.py` has no warnings mechanism today (unlike
`check.py`/`index.py`), and introducing one for two checks would be disproportionate new
infrastructure. This matches the existing `BROKEN_RELATED_LINK`'s severity exactly, so no
new severity concept is introduced.

Two codes, not three: `missing_targets()` alone would suggest a third
`MISSING_RELATIONSHIP_TARGET` code distinct from `BROKEN_SUPERSESSION_LINK`, but a missing
supersession target *is* a broken supersession link — one code covers it.

## Testing

- `tests/unit/test_globs.py`/`test_conflict.py` — extended for `globs.path_under()`;
  existing `conflict.affected_paths_overlap` tests must pass unmodified after the refactor.
- `tests/unit/test_query.py` — `matches_keyword` (title-only, body-only, neither),
  `matches_tags_any`, `matches_paths_exact`, `path_governed_by` (directory-boundary
  prefix, glob, and non-match cases), `rank_key` ordering across all five tiers.
- `tests/unit/test_relationships.py` — `resolve()` produces the expected edge list;
  `missing_targets()`/`supersession_mismatches()` against fixture data with a dangling
  target and a one-sided supersession.
- `tests/unit/test_search_command.py` — keyword-in-title, keyword-in-body, tag filter
  (OR within field), AND across different fields, status filter, `--path` using governed-by
  semantics, no-filter-returns-all, `--limit`/`total`/`truncated`, `matched_in` correctness,
  deterministic ordering, malformed-ADR warning.
- `tests/unit/test_related.py` — new regression test: keyword present only in body now
  matches; all existing tests unmodified and still passing (policy unchanged).
- `tests/unit/test_index.py` — Relationships section renders a supersession chain and a
  related list with titles; an ADR with no relationships is absent from the section.
- `tests/unit/test_validate.py` — `BROKEN_SUPERSESSION_LINK` for a dangling supersedes/
  superseded_by target; `SUPERSESSION_MISMATCH` for a one-sided edit; the real repository's
  own 10 ADRs still validate clean (no existing supersession is broken).
- `tests/unit/test_locale.py` — extended to cover the five new keys in the existing
  8-catalog exact-key-set parity check.
- `tests/integration/test_localized_workflow.py` or equivalent — `search` and the new
  index section produce valid output in at least one non-English locale.

## Documentation

- `README.md` — add `search` alongside the existing `related`/`check` usage examples,
  including the explicit AND/OR filter-semantics statement.
- `skills/adr-toolkit/SKILL.md` — document when an agent should reach for `search` versus
  `related` (ad-hoc lookup vs. DISCOVER-stage conflict check), framed as: `related` is a
  discovery *policy* built on the same Query Engine `search` uses generically.
- Run every newly documented command in a scratch repository before treating the docs as
  accurate, matching this project's existing practice.

## Implementation sequencing

1. Extract `_path_under` from `rules/conflict.py` into `core/globs.py` as
   `globs.path_under()`; refactor `conflict.affected_paths_overlap` to call it. Full
   `test_conflict.py`/`test_check.py` suites must still pass unmodified — pure refactor,
   no behavior change.
2. `core/query.py` + tests (no command changes yet).
3. `core/relationships.py` + tests (no command changes yet).
4. `related.py` migrated onto `core/query.py`, body-search regression test added — verify
   all existing tests still pass unmodified.
5. `search` command + CLI wiring + tests.
6. `index.py` Relationships section + 8-locale catalog updates + tests.
7. `validate.py` relationship-integrity checks + tests, run against this repository's real
   10 ADRs to confirm no existing supersession is inadvertently flagged.
8. Docs (README, SKILL.md) + a real scratch-repo run of every newly documented command.
9. Full suite + `sync_version.py --check` + `adr.py validate`/`index` against this
   repository's real ADRs.
