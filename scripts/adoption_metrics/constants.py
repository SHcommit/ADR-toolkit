"""Shared constants for ADR adoption metrics."""

import re

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)
REQUIRED_EXCEPTION_FIELDS = {
    "id",
    "adr_id",
    "rule_id",
    "owner",
    "reason",
    "scope",
    "created",
    "expiry",
}
EXCEPTION_FIELD_TYPES = {
    "id": str,
    "adr_id": str,
    "rule_id": str,
    "owner": str,
    "reason": str,
    "scope": list,
    "created": str,
    "expiry": str,
}
EXCEPTION_ID_RE = re.compile(r"^EXC-\d{4}$")
ADR_ID_RE = re.compile(r"^ADR-\d{4}$")
DATE_ONLY_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EVENT_REQUIRED_FIELDS = {
    "adr_created": {"adr_id", "status"},
    "adr_status_changed": {"adr_id", "from", "to"},
    "review_requested": {"adr_id", "reviewer", "review_cycle"},
    "review_submitted": {"adr_id", "reviewer", "review_cycle", "qualified"},
    "violation_observed": {"fingerprint", "adr_id", "rule_id"},
    "violation_resolved": {"fingerprint", "adr_id", "rule_id"},
}
GITHUB_REVIEW_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 100, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes {
        id
        number
        author { login }
        files(first: 100) { nodes { path } pageInfo { hasNextPage } }
        timelineItems(
          first: 100,
          itemTypes: [REVIEW_REQUESTED_EVENT, PULL_REQUEST_REVIEW]
        ) {
          nodes {
            __typename
            ... on ReviewRequestedEvent {
              createdAt
              requestedReviewer {
                __typename
                ... on User { login }
                ... on Team { slug }
                ... on Mannequin { login }
              }
            }
            ... on PullRequestReview {
              submittedAt
              author { login }
            }
          }
          pageInfo { hasNextPage }
        }
      }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""
