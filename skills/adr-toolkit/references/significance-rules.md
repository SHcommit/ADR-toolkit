# Significance Scoring Reference

RECORD scores a candidate decision against 7 criteria, each 0/1/2, then
calls `python3 skills/adr-toolkit/scripts/adr.py significance --input scores.json --json`
from the repository root to get a deterministic band. The agent decides
each score; the script only sums and bands them, so the same inputs always
produce the same recommendation.

## The 7 criteria

- `reversal_cost` - how expensive would it be to undo this later?
- `alternatives_considered` - were there multiple realistic options, or
  effectively one obvious choice?
- `quality_attribute_impact` - does this meaningfully affect performance,
  reliability, security, or another quality attribute?
- `boundary_or_pattern_change` - does this change a system boundary or a
  pattern other code is expected to follow?
- `multi_developer_relevance` - will other developers (or agents) need to
  follow this going forward?
- `ops_security_data_impact` - does this affect operations, security, or
  data consistency?
- `future_rationale_query_likelihood` - is someone likely to ask "why did
  we do it this way" months from now?

Score each criterion 0 (no), 1 (somewhat), or 2 (clearly yes) based on the
actual code and conversation - never guess a score to force a particular
band. If a criterion is omitted from the input, the scoring script treats it
as 0. Values other than 0, 1, or 2 are invalid.

## Bands

- 0-3: `not_needed` - recommend a commit message or code comment instead.
- 4-6: `optional` - mention the option to the user, let them decide.
- 7-14: `recommended` - proceed to drafting an ADR.

The score is a decision aid, not a verdict the user cannot override. If a
user insists on recording something scored `not_needed`, defer to them
rather than refusing.
