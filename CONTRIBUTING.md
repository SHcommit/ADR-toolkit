# Contributing

Thanks for helping improve ADR Toolkit. This project is intentionally small:
the agent can reason and draft, but deterministic scripts own file writes,
IDs, lifecycle transitions, validation, indexes, and machine-readable output.

## Branches

Follow the repository policy in `AGENTS.md`.

- Branch from `develop` for normal work.
- Use `feature/*`, `fix/*`, or `docs/*` for short-lived work branches.
- Merge normal work back to `develop` through a pull request.
- Release branches merge to `master` and back to `develop`.
- Tags named `v*` are created only from `master`.

## Local Checks

Run the relevant checks before opening a pull request:

```bash
python3 -m pytest -q
python3 scripts/sync_version.py --check
python3 skills/adr-toolkit/scripts/adr.py validate --dir docs/decisions --json
python3 skills/adr-toolkit/scripts/adr.py index --dir docs/decisions --json
```

For changes that may affect accepted architectural decisions, also run:

```bash
python3 skills/adr-toolkit/scripts/adr.py check --uncommitted --dir docs/decisions --json
```

## ADR Changes

- Keep ADR source files flat under `docs/decisions/`.
- Do not hand-edit generated indexes or lifecycle links to repair validation
  errors. Change the source ADR or use the lifecycle command.
- Use `adr.py create`, `status`, `deprecate`, `supersede`, and `exception` for
  deterministic mutations.
- Accepted ADRs are append-only in spirit: use supersession for changed
  decisions instead of rewriting history.

## Public Repository Hygiene

Public repository branch/tag protection is expected to enforce PRs, required
checks, conversation resolution, and force-push/deletion restrictions on
`develop`, `master`, and `v*` tags once the repository is public.
