# MADR Template Guide

## When to use `madr-minimal.md`

- The decision has two or fewer realistic alternatives.
- No conflicting quality attributes need a comparison table.
- The project is small enough that a short record is genuinely sufficient.

## When to use `madr-full.md`

- Three or more alternatives were seriously considered.
- Different options trade off against each other on quality attributes
  (e.g. latency vs. operational complexity).
- The decision affects multiple teams, services, or systems.

## Section meaning

- **Context and Problem Statement** — the forces and constraints that made
  a decision necessary; not a restatement of the chosen solution.
- **Considered Options** — every realistic option actually evaluated, not
  a strawman list.
- **Decision Outcome** — the chosen option and the primary reason, stated
  as a single sentence a newcomer could quote.
- **Consequences** — both the benefit and the accepted cost; a decision
  with no listed downside has not been examined honestly.
- **Confirmation** — how someone (human or agent) can verify the decision
  is actually being followed in the code today.
- **Revisit Triggers** — concrete conditions, not vague ones like "if
  requirements change."
