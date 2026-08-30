# improvements.md

Backlog for follow-up improvements that are useful but not required to resume
the current session.

## Open

- [ ] **Decide branch integration.** `feat/adr-toolkit-mvp-implement` is
  pushed to `origin` but not merged to `master`, and no PR is open yet.
  Options: merge locally, open a PR, or leave as-is longer.
- [ ] **Clean up the stale remote branch** `origin/SHcommit/feat-plan-adr-toolkit`
  — left over from before the local rename to
  `feat/adr-toolkit-mvp-implement`; delete it on `origin` once confirmed
  it's not needed (e.g. no open PR references it).
- [ ] `scripts/adr.py`'s `--json` flag is parsed on every subcommand but never
  read (output is always JSON regardless). Either implement a non-JSON
  mode or drop the flag.
- [ ] Codex's `quick_validate.py` rejects the existing ADR Toolkit `SKILL.md`
  frontmatter keys `user-invocable` and `version`, while the repository's
  cross-harness contract and tests currently require them. Make a deliberate
  metadata/validator compatibility decision before changing either side;
  do not silently delete the keys to satisfy one harness.
- [ ] **CHECK follow-ups** — see `project-roadmap.md`'s "CHECK follow-ups"
  section: a `git ls-files`-based existing-paths check (perf +
  `.gitignore` correctness), collapsing the `SKIP_FILES`/ADR-loading loop
  duplicated across 4 command modules, documenting that `pattern` syntax
  differs by rule kind, `diff.py` rename handling, and two narrow
  `diff.py` edge cases. None blocking.
- [ ] **i18n/adapters/release follow-ups** — see `project-roadmap.md`'s
  "i18n, adapters, release follow-ups" section: the Codex adapter README
  slightly overclaims which manifest its verification exercised (see the
  standing risk in `handoff.md`), its install step 1 (the `skills/`
  symlink) is currently orphaned relative to the documented working
  install path, description text has drifted across 4 manifests with no
  sync mechanism, and a few narrower `sync_version.py`/CI polish items.
  None blocking.

## Done

Historical detail now lives in `changelog.md` (what shipped) and git log
(how) — this section stays empty going forward rather than duplicating
that record across three files.
