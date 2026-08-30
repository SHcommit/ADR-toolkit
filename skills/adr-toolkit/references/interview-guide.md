# Interview Guide

RECORD and DISCOVER ask at most 3 questions per round. Fewer is better:
never ask a question `discover`, `related`, the repository, or the user's
request already answered. Authority or time pressure is not a reason to
exceed this per-round cap; prioritize the highest-value unanswered questions
and continue in a later round when needed.

## Priority order

Ask the highest-priority unanswered question first:

Each independently answerable priority item counts as one substantive
question. Do not combine multiple priority items in one sentence or bullet
to bypass the cap; after three substantive questions, defer lower-priority
items to a later round.

1. What problem or constraint made this decision necessary?
2. What realistic alternatives were considered?
3. Why was this option chosen over the others - what was the primary driver?
4. What negative consequence was knowingly accepted?
5. What condition should cause this decision to be revisited?

## What not to ask

- A library name or version already visible in a dependency manifest -
  `discover`/`related` already reported it.
- A policy already stated in an existing ADR - cite it instead.
- A preference with no effect on the file that gets written (for example,
  writing style opinions).
- Anything the user already stated in their own request.

## If the user's answer is ambiguous

Do not treat an ambiguous answer as complete or advance to lower-priority
questions. Ask one focused follow-up first rather than guessing. That
follow-up still counts against the 3-question cap for the round.
