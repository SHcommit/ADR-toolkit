# Generic harness adapter

If your AI coding harness isn't Claude Code, Codex, Gemini CLI, or
Antigravity CLI, ADR Toolkit still works — `SKILL.md` only assumes your
harness can read project instructions and run shell commands, which
covers effectively every current coding agent, including ones this
project hasn't been tested against yet.

## Install

1. Copy or symlink `skills/adr-toolkit/` into your project, at whatever
   path your harness scans for instructions or skills:

   ```bash
   mkdir -p .agents/skills
   ln -s ../../path/to/adr-toolkit/skills/adr-toolkit .agents/skills/adr-toolkit
   ```

2. Add one line to your project's `AGENTS.md` (or whatever instruction
   file your harness reads first):

   ```markdown
   For architecture decisions (introducing, recording, or checking ADRs),
   follow `.agents/skills/adr-toolkit/SKILL.md`.
   ```

3. That's it. `SKILL.md` never assumes a plugin manifest, a hook, or any
   harness-specific configuration — only that something can read markdown
   and run `python scripts/adr.py ...`.

## No agent at all?

You don't need one. Every deterministic operation is a plain CLI command
you can run yourself: `python skills/adr-toolkit/scripts/adr.py init`,
`... validate`, `... index`, and `... create --interactive` (see Task 19)
for a guided prompt sequence that needs no AI harness whatsoever.
