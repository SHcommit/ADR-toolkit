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
never are. See [`examples/quickstart.md`](examples/quickstart.md) for a
full INIT → RECORD → CHECK walkthrough with real command output, or
[`docs/decisions/`](docs/decisions/) for this toolkit's own dogfooded ADRs.

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
structurally provable rules in the selected diff:

| Meaning | Existing JSON result |
|---|---|
| `VERIFIED` | `related`, only for applicable explicit rules that were evaluated |
| `VIOLATED` | `verified_violation` |
| `UNVERIFIABLE` | `review_required` or `no_applicable_constraint` |
| `NOT_APPLICABLE` | No known ADR/rule applies to the selected change |

Warnings mean some evidence could not be evaluated and must be reported. A
clean result never proves prose rationale, runtime behavior, or every
architecture invariant.

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
