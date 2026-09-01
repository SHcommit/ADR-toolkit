## PR Title Format

Please ensure your PR title follows Conventional Commits format:
`type(scope): description` (e.g. `feat(cli): add discover command`, `fix(check): fix unicode path matching`)

Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`

---

## Summary

- 

## Examples Impact (Mandatory for `feat:` and `fix:`)

- [ ] `feat:` or `fix:` PR: I updated/added `examples/` and `examples/ko/` guides.
- [ ] I verified examples execution via `python3 scripts/verify_examples.py --check`.
- [ ] Non-feature change (`docs:`, `chore:`, `ci:`): No example changes needed.

## ADR Impact

- [ ] I checked whether this changes an accepted architectural decision.
- [ ] I linked related ADRs, or this PR has no ADR impact.
- [ ] I ran `adr.py check` when the change touches governed paths.

Related ADRs:

## Verification

- [ ] `python3 -m pytest -q`
- [ ] `python3 scripts/verify_examples.py --check`
- [ ] `python3 scripts/sync_version.py --check`
- [ ] `python3 skills/adr-toolkit/scripts/adr.py validate --dir docs/decisions --json`
- [ ] `python3 skills/adr-toolkit/scripts/adr.py index --dir docs/decisions --json`

## Notes

- 
