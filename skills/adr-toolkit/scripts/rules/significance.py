"""Deterministic significance classification for RECORD.

The agent scores each of the 7 criteria itself (0, 1, or 2) based on its own
reading of the code and conversation — that judgment is not scriptable. This
module only sums and bands the result deterministically, so the same 7
scores always produce the same recommendation.
"""

CRITERIA = (
    "reversal_cost",
    "alternatives_considered",
    "quality_attribute_impact",
    "boundary_or_pattern_change",
    "multi_developer_relevance",
    "ops_security_data_impact",
    "future_rationale_query_likelihood",
)


def score(criteria_scores: dict) -> int:
    total = 0
    for criterion in CRITERIA:
        value = criteria_scores.get(criterion, 0)
        if value not in (0, 1, 2):
            raise ValueError(f"{criterion} must be 0, 1, or 2, got {value!r}")
        total += value
    return total


def classify(total: int) -> str:
    if total <= 3:
        return "not_needed"
    if total <= 6:
        return "optional"
    return "recommended"
