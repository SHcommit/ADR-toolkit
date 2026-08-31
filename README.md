# ADR Toolkit

An agent-native Architecture Decision Record toolkit: it inspects your
repository and existing decisions before asking questions, records new
decisions with a human-approved MADR, and checks a diff against Accepted
decisions for structural conflicts — all before anything gets written.

Kafka got introduced into a production system once, and the person who
made that call left the company. Nobody could say why Kafka was chosen
over the alternatives, what problem it solved, or what was consciously
traded away. ADR Toolkit exists so that, going forward, the *reason*
behind a structural decision survives as long as the code does — written
by inspecting the repository first, not invented, and findable by a
successor (human or agent) in under a minute.

## What it does

| Operation | What it does |
|---|---|
| **INIT** | Scaffolds `docs/decisions/` in a repo that has none yet — directory, template, and ADR-0001. |
| **DISCOVER** | Mines existing conventions (dependency manifests, code, git history) for past decisions that were never written down, and drafts retrospective ADRs for ones you approve. |
| **RECORD** | Captures a new decision — before or after implementing it — investigating the code first and asking only what it can't answer (max 3 questions). |
| **CHECK** | Matches a diff against Accepted ADRs' structured `constraints:` rules and reports Related / Review required / Verified violation / No applicable constraint — never picks a fix for you. |

Every file write goes through a deterministic script and is shown to a
human before it happens. Judgment (what's significant, what to ask, how to
draft) is the agent's job; file writes, ID assignment, and validation
never are. See [`examples/`](examples/) for real-world usage examples ([Basic usage](examples/basic-usage.md), [Constraint enforcement](examples/check-constraints.md), [Dependency graphs](examples/graph-visualization.md), [Multilingual ADRs](examples/multilingual-adr.md), and [Quickstart](examples/quickstart.md)), or [`docs/decisions/`](docs/decisions/) for this toolkit's own dogfooded ADRs.

## Install

`skills/adr-toolkit/` is one self-contained, harness-agnostic package —
copy or symlink it wherever your harness looks for skills, then point one
of these adapters at it:

| Harness | Depth | Install |
|---|---|---|
| [Claude Code](.claude-plugin/) | Full plugin, auto-discovered | Add this repo via `.claude-plugin/marketplace.json` |
| [Codex CLI](adapters/codex/) | Agent Plugins 1.0.0 manifest | [`adapters/codex/README.md`](adapters/codex/README.md) |
| [Gemini CLI](adapters/gemini-cli/) | Extension manifest | [`adapters/gemini-cli/README.md`](adapters/gemini-cli/README.md) |
| [Antigravity CLI](adapters/antigravity/) | Plugin manifest | [`adapters/antigravity/README.md`](adapters/antigravity/README.md) |
| Anything else | Generic fallback | [`adapters/generic/README.md`](adapters/generic/README.md) — needs only markdown-reading and shell |

**No AI harness at all?** `create --interactive` runs the same interview
directly in a terminal — no agent required:

```bash
python skills/adr-toolkit/scripts/adr.py create --interactive --dir docs/decisions --json
```

## Language and repository config

ADR Toolkit localizes deterministic, code-owned text in eight canonical
locales: `en`, `ko`, `ja`, `zh`, `fr`, `es`, `de`, and `pt-BR`. `zh` means
Simplified Chinese. User-authored prose is preserved as written, while JSON
keys, status values, error codes, IDs, and filenames remain machine-stable.

Choose the repository default during INIT:

```bash
python skills/adr-toolkit/scripts/adr.py init --locale ko --dir docs/decisions --json
```

This creates `.adr-toolkit.json` at the repository root:

```json
{
  "schema_version": 1,
  "locale": "ko"
}
```

Commands then use the repository default without repeating `--locale`:

```bash
python skills/adr-toolkit/scripts/adr.py create --interactive --dir docs/decisions --json
python skills/adr-toolkit/scripts/adr.py index --dir docs/decisions --json
```

An explicit flag overrides the repository default for one operation. Input
draft locale overrides the repository only when the CLI flag is absent:

```bash
python skills/adr-toolkit/scripts/adr.py create --locale ja --interactive --dir docs/decisions --json
python skills/adr-toolkit/scripts/adr.py index --locale fr --dir docs/decisions --json
```

The effective CLI order is explicit flag → approved input draft → repository
default → `en`. Unsupported locales and malformed config fail visibly.

### Unicode titles and portable filenames

Titles and bodies remain Unicode. Filenames remain ASCII for filesystem, URL,
and Git portability. For the title `결제 시스템 분리`, an agent can propose a
meaningful slug and show it for human approval:

```bash
python skills/adr-toolkit/scripts/adr.py create --input draft.json \
  --slug separate-payment-system --dir docs/decisions --json
```

The deterministic core validates the slug and creates a filename such as
`0002-separate-payment-system.md`. It never translates or transliterates the
title itself. Without an approved slug or an ASCII fragment in the title, a
fresh repository safely falls back to `0001-decision.md`.

## CHECK confidence

CHECK does not certify the entire architecture. It evaluates only explicit,
structurally provable rules in the selected diff. Every finding carries a
`confidence` field with one of these four values directly — no need to
re-derive it from `kind`:

| `confidence` | `kind` it comes from | Meaning |
|---|---|---|
| `VERIFIED` | `related` | Applicable explicit rules were evaluated and none fired. |
| `VIOLATED` | `verified_violation` | Structural evidence confirms a violation. |
| `UNVERIFIABLE` | `review_required` or `no_applicable_constraint` | No usable rule vocabulary could prove or disprove this. |
| `NOT_APPLICABLE` | (no finding at all) | No known ADR/rule applies to the selected change — an empty `findings` list, not proof of compliance. |

Warnings mean some evidence could not be evaluated and must be reported. A
clean result never proves prose rationale, runtime behavior, or every
architecture invariant.

### Exceptions

`register_exception` — one of a Verified violation's five resolutions — is a
real, deterministic record, not just a label:

```bash
python skills/adr-toolkit/scripts/adr.py exception --input exception.json \
  --dir docs/decisions --json
```

`exception.json` requires `adr_id`, `rule_id`, `owner`, `reason`, a `scope`
(path patterns the exception is narrowed to), and an `expiry`
(`YYYY-MM-DD`). The command assigns the next `EXC-NNNN` id and writes
`docs/decisions/exceptions/NNNN.json`. CHECK annotates a matching, non-expired
exception onto its finding's `exception` field — the finding's `kind` and
`confidence` stay exactly what the structural evidence says
(`verified_violation`/`VIOLATED`); an exception is visible, reviewable
evidence, never a silent pass. Once `expiry` passes, CHECK stops applying it
automatically.

## Search

Find an existing ADR by keyword (title **and** body), tags, status, or the
file path it governs — without opening every file:

```bash
python skills/adr-toolkit/scripts/adr.py search --keyword architecture --dir docs/decisions --json
```

```json
{
  "ok": true,
  "operation": "search",
  "query": {"keyword": "architecture", "tags": null, "status": null, "path": null, "limit": null},
  "count": 1,
  "total": 1,
  "truncated": false,
  "results": [
    {
      "id": "ADR-0001",
      "filename": "0001-record-architecture-decisions.md",
      "path": "docs/decisions/0001-record-architecture-decisions.md",
      "title": "Record architecture decisions",
      "status": "accepted",
      "tags": ["process"],
      "matched_in": ["title", "body"]
    }
  ],
  "warnings": []
}
```

**Filter semantics:** filters across different fields (`--id`, `--keyword`,
`--tags`, `--status`, `--path`) are combined with AND. Multiple values within
`--tags` are combined with OR — `--tags postgres mysql` means "postgres or
mysql". No filters at all browses every ADR. `--id` looks up one ADR by its
exact id. `--path` matches a real file against an ADR's governed scope (the
same directory-boundary + glob logic CHECK uses), not an exact match against
the ADR's literal `affected_paths` list. `--limit N` truncates the
already-ranked (best-match-first) result list; `total` is always the
untruncated count and `truncated` is `total > count`.

`search` is a general lookup command ("has this been decided before?"), distinct
from `related` (used during RECORD's DISCOVER stage to find precedent for a
*new* draft, with a broader OR-across-fields match).

## Relationship graph

`index` embeds a Mermaid relationship graph in `docs/decisions/README.md`
whenever ADRs have `related` or `supersedes` links, so GitHub can render the
navigation view directly.

For a standalone graph artifact, export Mermaid and SVG files:

```bash
python skills/adr-toolkit/scripts/adr.py graph --dir docs/decisions --format both --json
```

This writes `docs/decisions/relationships.mmd` and
`docs/decisions/relationships.svg`. SVG is the default image artifact because it
stays sharp when zoomed and does not require Mermaid CLI, Node, or a browser.
With `--format both`, `--output build/adr-relationships` is treated as a file
prefix and writes `build/adr-relationships.mmd` plus
`build/adr-relationships.svg`; relative output paths are resolved from
`--root`, matching the other repository-scoped commands.

### Why storage stays flat

ADRs live as `NNNN-slug.md` in one flat `docs/decisions/` directory — no
per-year, per-team, or per-status subfolders — no matter how many
accumulate. Two comparable real-world tools were checked before deciding
this: [`npryce/adr-tools`](https://github.com/npryce/adr-tools), the
original Nygard-style CLI, ships no search at all and expects `grep`; the
most-adopted actively maintained ADR tool,
[`log4brains`](https://github.com/thomvaill/log4brains) (1.5k+ GitHub
stars), also keeps ADRs as flat Markdown and instead layers a full-text
search and a relationship graph on top — it does not shard the source
files by count. A folder hierarchy also creates a real problem flat storage
avoids: a decision that spans two teams or domains has no unambiguous
folder to live in.

The corollary is **retrieval, not storage, is where a growing ADR set gets
harder to use** — so that's where the effort went: `search`'s
title-and-body keyword/tag/status/path matching plus the generated index's
"By status" / "By tag" / "By affected path" / "Relationships" views. Both
already work identically for 10 ADRs or 500. Folder sharding, a rendered
relationship graph, and a real search index are deliberately not built yet
— they're tracked in [`project-roadmap.md`](project-roadmap.md), gated on
this repository (or an adopting team's) ADR count actually reaching a scale
where flat-directory substring search stops being fast enough. Building
that ahead of evidence would add real maintenance cost for a problem no one
has hit yet.

## Scope

- MADR 4.x format, no new standard.
- CHECK's MVP conflict detection is structural evidence only
  (`constraints:` blocks) — no semantic/AST analysis. See
  [ADR-0002](docs/decisions/0002-limit-check-s-conflict-detection-to-structural-evidence-only.md).
- Deterministic INIT, CREATE, and INDEX structure ships in eight locales;
  agent-composed and user-authored prose is never machine-translated by the
  core. See
  [ADR-0006](docs/decisions/0006-localized-adr-generation.md).
- Everything explicitly deferred out of MVP is tracked in
  [`project-roadmap.md`](project-roadmap.md), not silently dropped.

## Contributing

Read [`AGENTS.md`](AGENTS.md) first — it's the shared operating document
every harness (and every human) working in this repo follows, including
the branch policy.

## License

[MIT](LICENSE)
