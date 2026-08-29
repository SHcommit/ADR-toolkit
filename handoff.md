# handoff.md

Current task:
- ADR Toolkit MVP, Plan 1 of 4 ("core scripts + INIT/DISCOVER") is fully
  implemented, reviewed clean (per-task review + final whole-branch review
  + one fix wave + scoped re-review, all clean), and committed on
  `SHcommit/feat-plan-adr-toolkit`. 73/73 tests pass. Branch kept as-is
  (not merged to `master`) and pushed to `origin` per user request.

Touched files (this round):
- `handoff.md`, `improvements.md` (this update)
- Everything under `skills/adr-toolkit/`, `adapters/`, `tests/`,
  `.github/workflows/test.yml`, `.claude-plugin/`, `.gitignore` (Plan 1
  implementation + final-review fixes, already committed)

Next step — in priority order:
0. **Execute Plan 2** (RECORD + lifecycle), now fully designed and
   committed at
   `docs/superpowers/plans/2026-08-30-adr-toolkit-record-and-lifecycle.md`
   (11 TDD tasks: significance scoring, related-ADR search,
   status/supersede/deprecate commands, SKILL.md RECORD/Lifecycle
   sections, one golden fixture test). Writing it consumed the remaining
   token budget for this session — execution (subagent-driven-development,
   ~11 implementer+reviewer dispatch pairs like Plan 1's) was deliberately
   deferred to a session with more budget. Nothing was executed; the plan
   document is the only new artifact.
1. **Confirm 3 open decisions before going further:**
   - License: MIT was proposed in the design spec (§13) while the user was
     away; needs explicit sign-off before any public release.
   - Final MVP scope: whether to keep 5 languages / 4 harnesses as
     originally agreed, or trim further (raised once, user hasn't answered
     yet — Plan 1 itself is unaffected either way, since it only built
     English + Claude Code).
   - Trivial: `adapters/generic/README.md` line 29 has a leftover bare
     `python scripts/adr.py` reference in prose (should say
     `python skills/adr-toolkit/scripts/adr.py` like the rest of the file)
     — noted by the final review as non-blocking, still unfixed.
2. **Write and execute Plan 2 (RECORD workflow):** significance scoring
   (0–14 scale, spec §8.3 lineage), related-ADR search, lifecycle CLI verbs
   (`status`/`supersede`/`deprecate`, spec's "Lifecycle operations"
   section), RECORD's dual forward-looking/retrospective support, the
   "what belongs in an ADR" classification table already shared with
   INIT/DISCOVER.
3. **Plan 3 (CHECK workflow):** structured `constraints:` YAML rule
   matching (spec §7), four-way finding classification (Related/Review
   required/Verified violation/No applicable constraint), five resolution
   options on a verified violation.
4. **Plan 4:** i18n wiring (5 locales) into the skill's runtime text,
   Codex/Gemini CLI/Antigravity CLI adapters (their manifest formats are
   NOT yet verified against real docs — the Claude adapter mistake found in
   final review, where the "skills" key and manifest location were wrong,
   is a concrete warning to verify before building these, not just guess),
   release automation (version sync, CHANGELOG, GitHub Release).
5. Decide when to make the GitHub repo actually public / promote it, given
   the stated goal of open-source adoption and stars.

Open risk:
- CHECK's conflict detection is scoped to structural/`constraints:`-block
  evidence only for MVP (semantic taxonomy deferred to
  `project-roadmap.md`) — an explicit trade already agreed with the user,
  not an oversight.
- Whichever future plan builds the Codex/Gemini CLI/Antigravity adapters
  must verify each harness's actual manifest/discovery convention against
  real documentation first — do not assume it mirrors Claude Code's.
