# Adoption Metrics Collector Design

## Context

`docs/enterprise-adoption.md` section 7 defines five operational metrics for
finding workflow bottlenecks and policy debt: decision lead time, review
latency, supersession rate, unresolved violations, and exception age. The ADR
Toolkit already stores the current ADR state in Markdown frontmatter and active
policy exceptions in JSON, but those snapshots do not preserve every event the
definitions require. In particular, a single `date` cannot represent both the
proposal and decision times, CHECK output is not persisted, and a file does not
identify when review was requested or completed.

The collector must not turn missing evidence into a plausible-looking number.
It will therefore separate metric calculation from evidence collection and
report provenance and coverage with every value. Git is the broadly portable
default history source. GitHub review events improve the common hosted case,
while a provider-neutral JSONL event contract supports GitLab, Bitbucket,
non-Git SCMs, and manually exported audit data.

## Goals

- Produce one deterministic JSON document covering all five section 7 metrics.
- Work without GitHub and degrade cleanly when Git or provider data is absent.
- Use local ADR and exception files as the current-state source of truth.
- Reconstruct lifecycle transitions from local Git when explicit events are
  absent.
- Use GitHub only to supply review events that local Git cannot represent.
- Accept the same events through JSONL so the calculation layer is not tied to
  a hosting provider.
- Make incomplete evidence visible through `available`, `coverage`, `sources`,
  and warnings instead of silently estimating missing history.
- Keep all existing ADR command modules unchanged.

## Non-goals

- Ranking people, teams, or repositories by productivity.
- Modifying ADR frontmatter, exception files, or Git history.
- Persisting CHECK observations during this first collector iteration.
- Supporting GitLab or Bitbucket APIs directly. Their exporters can target the
  provider-neutral event contract.
- Treating an active exception as resolution of a `VIOLATED` finding. Existing
  CHECK semantics deliberately annotate rather than hide violations.
- Calculating stale review coverage, which section 7 lists separately but the
  requested backlog item does not include.

## Architecture

The implementation is a single repository tool, `scripts/adoption_metrics.py`,
split internally into four boundaries:

1. Local readers parse ADR frontmatter, exception JSON, and optional historical
   CHECK observation files without importing the skill-internal `scripts`
   package.
2. Collectors normalize explicit JSONL, local Git history, and optional GitHub
   review data into provider-neutral events.
3. Pure calculation functions consume current records and normalized events.
4. The CLI validates arguments, assembles evidence in precedence order, and
   serializes the result.

The dependency direction is one-way:

```text
ADR / exceptions -----------+
explicit JSONL events ------+--> normalized records --> metric calculators --> JSON
local Git history ----------+
optional GitHub review data +
```

Metric calculators never invoke Git or GitHub. This keeps edge cases testable
without network access and prevents provider-specific fields from becoming part
of the public metrics contract.

## Command Interface

```text
python3 scripts/adoption_metrics.py \
  --root . \
  --dir docs/decisions \
  [--since 2026-01-01] \
  [--until 2026-12-31] \
  [--events path/to/events.jsonl] \
  [--github] \
  [--check-results path/to/check-observations.jsonl] \
  --json
```

`--root` defaults to the current directory and `--dir` is resolved beneath it.
`--until` defaults to the current UTC date; `--since` defaults to the earliest
available evidence. `--json` is required in v1 so no unstable human-readable
format becomes an accidental contract.

Local Git collection is attempted when `--root` belongs to a Git repository.
Absence of Git is not an error. `--github` opts into review collection through
the installed and authenticated `gh` CLI; failure becomes a warning unless the
entire requested metric has no other evidence. Explicit `--events` always works
without Git or GitHub.

All timestamps are parsed as ISO 8601. Date-only inputs represent midnight UTC
for interval filtering and whole-day age calculations. Invalid inputs produce a
non-zero exit and a JSON error object; an individual malformed ADR, exception,
or event becomes a warning while other valid records are still processed.

## Normalized Events

Each line of `--events` and `--check-results` is one JSON object with a versioned
envelope:

```json
{
  "schema_version": 1,
  "event": "adr_status_changed",
  "occurred_at": "2026-08-30T11:36:40Z",
  "adr_id": "ADR-0003",
  "from": "accepted",
  "to": "superseded",
  "source": "git"
}
```

Supported event names are:

| Event | Required payload | Purpose |
| --- | --- | --- |
| `adr_created` | `adr_id`, `status` | Establish first known lifecycle state |
| `adr_status_changed` | `adr_id`, `from`, `to` | Establish decision and supersession transitions |
| `review_requested` | `adr_id`, `reviewer`, `review_cycle` | Start review latency |
| `review_submitted` | `adr_id`, `reviewer`, `review_cycle`, `qualified` | End review latency at first qualified review |
| `violation_observed` | `fingerprint`, `adr_id`, `rule_id` | Open or continue a violation |
| `violation_resolved` | `fingerprint`, `adr_id`, `rule_id` | Close a previously observed violation |

Event identity is the tuple of event type, occurrence time, and its natural
entity key. Duplicate events from explicit input, Git reconstruction, and
GitHub are deduplicated. Evidence precedence is explicit JSONL, then local Git,
then GitHub. A higher-precedence event wins when two sources disagree, and the
conflict is emitted as a warning.

`review_cycle` is a provider-neutral, opaque string shared by every request and
submission belonging to one review cycle. Provider adapters must not expose a
pull-request number directly; the GitHub collector hashes its provider node ID
into a stable opaque cycle key.

## Git And GitHub Collection

The Git collector follows each `docs/decisions/[0-9]*.md` path through history,
parses frontmatter at every content-changing commit, and emits creation and
status-transition events using the commit author timestamp. It does not infer a
`proposed` event for an ADR whose first committed state is `accepted`; that ADR
is excluded from lead-time coverage. Rename following is best effort and emits
a warning if an ADR ID changes.

The GitHub collector paginates through pull requests and selects review cycles
completed during the requested interval after normalization. A review is
qualified when it is submitted by a reviewer
who was explicitly requested for that pull request; self-review by the PR author
does not qualify. The first qualified submitted review after the first review
request ends the interval. The normalized event keeps no provider-specific URL
or numeric ID in the calculation path, though diagnostics may report them.

GitHub collection is an enhancement, not a prerequisite. Repositories on other
providers can export equivalent `review_requested` and `review_submitted`
events. A repository with neither source receives an unavailable review metric,
not a guessed value.

If GitHub truncates the file or timeline connection inside any pull request,
the collector discards GitHub review evidence for that run and emits a warning;
partial provider evidence must not produce a confident latency.

## Metric Definitions

### Decision Lead Time

For each ADR, measure elapsed hours from its earliest observed `proposed` state
to its first transition into `accepted` or `rejected`. Report the median across
decisions completed within `[since, until]`. ADRs first observed in a terminal
state are excluded and reduce coverage.

### Review Latency

For each ADR review cycle, measure elapsed hours from the first review request
to the first subsequent qualified review. Report the median for review cycles
completed within the interval. Requests with no qualified review are reported
as open review cycles but are not included in the median.

### Supersession Rate

The denominator is the cohort of ADRs first observed as `accepted` or
transitioning to `accepted` within the interval. The numerator is the members
of that same cohort that also transition to `superseded` within the interval.
Report a JSON number in the range 0 through 1, or `null` when the denominator is
zero. Also report both raw counts so consumers do not over-interpret a small
sample.

### Unresolved Violations

A violation is identified by the stable fingerprint supplied by the CHECK
observation producer. It is open after its latest `violation_observed` event and
closed after a later `violation_resolved` event. At `until`, report the open
count and each open violation's whole-day age from first uninterrupted
observation. `--check-results` is a current snapshot: count is available, but
age is unavailable unless matching historical observations are supplied with
`--events`. An empty `--check-results` file is an authoritative snapshot with
zero open violations, not missing evidence. Active exceptions remain visible
and do not close violations.

### Exception Age

For every schema-valid exception, calculate whole days from `created` to
`until`. Report active exception count, median active age, maximum active age,
and count whose `expiry` is before `until`. Expired exceptions are excluded from
active-age aggregates but included in the expired count.

## Output Contract

```json
{
  "ok": true,
  "operation": "adoption_metrics",
  "schema_version": 1,
  "period": {"since": "2026-01-01", "until": "2026-12-31"},
  "metrics": {
    "decision_lead_time": {
      "available": true,
      "median_hours": 26.5,
      "sample_size": 4,
      "coverage": {"eligible": 5, "measured": 4, "ratio": 0.8},
      "sources": ["git"]
    },
    "review_latency": {
      "available": false,
      "median_hours": null,
      "sample_size": 0,
      "coverage": {"eligible": 0, "measured": 0, "ratio": null},
      "sources": [],
      "reason": "No review events were available."
    },
    "supersession_rate": {
      "available": true,
      "rate": 0.25,
      "superseded": 1,
      "accepted": 4,
      "sources": ["git"]
    },
    "unresolved_violations": {
      "available": true,
      "open_count": 2,
      "age_available": true,
      "median_age_days": 3,
      "max_age_days": 5,
      "sources": ["events"]
    },
    "exception_age": {
      "available": true,
      "active_count": 2,
      "median_age_days": 9.5,
      "max_age_days": 12,
      "expired_count": 1,
      "sources": ["exceptions"]
    }
  },
  "warnings": []
}
```

Metric objects keep stable names even when unavailable. `available: false`
requires a machine-readable `reason`; numeric values remain `null`. A source is
listed only if it contributed evidence to that metric. Warnings contain stable
codes plus file/event context and never go to stdout outside the JSON document.

## Error Handling And Safety

The collector is read-only. It does not rewrite ADRs, exceptions, events, or
Git metadata. Paths are resolved beneath `--root`; path escape is rejected.
Subprocess calls use argument arrays and never invoke a shell. GitHub tokens are
left to `gh` credential management and never appear in output.

Missing optional sources degrade metric availability. Invalid CLI arguments,
an absent ADR directory, path escape, or failure to serialize the final result
is fatal. Malformed individual records are warnings because discarding every
metric would hide otherwise valid evidence; their omission is reflected in
coverage.

## Testing Strategy

`tests/unit/test_adoption_metrics.py` loads the repository-root module with
`importlib.util.spec_from_file_location`, matching
`tests/unit/test_sync_version.py`, because the distributable skill has an
unrelated top-level `scripts` package.

Tests use temporary ADR directories, synthetic Git repositories, inline JSONL,
and pure normalized GitHub response fixtures. No test requires network access
or a logged-in GitHub account. TDD cycles cover:

- current ADR and exception parsing, including malformed-record warnings;
- Git lifecycle reconstruction without inventing missing proposed history;
- event deduplication and precedence;
- qualified review selection and open review cycles;
- all five calculations, empty denominators, median behavior, and interval
  boundaries;
- partial availability and coverage reporting;
- deterministic CLI JSON and fatal error JSON;
- operation without Git, GitHub, or event history;
- path containment and subprocess argument safety.

The focused unit file runs first. Final verification runs the full unit and
integration suites plus the repository's strict type check and any formatting
or lint checks configured for scripts.

## Files And Scope

Implementation creates:

- `scripts/adoption_metrics.py`
- `tests/unit/test_adoption_metrics.py`

This design document and the normal closeout updates to `changelog.md`,
`handoff.md`, and `improvements.md` are the only other expected changes. No
file under `skills/adr-toolkit/scripts/commands/` is modified.
