"""Small deterministic evaluators used by tests and the local runner."""

from collections import Counter
from typing import Any

from pydantic import BaseModel, Field

from backend.graph.rag.service import RagResult


class EvaluationScore(BaseModel):
    passed: bool
    details: dict[str, Any] = Field(default_factory=dict)


def evaluate_exact_route(*, expected: str, actual: str) -> EvaluationScore:
    return EvaluationScore(
        passed=expected == actual,
        details={"expected": expected, "actual": actual},
    )


def evaluate_tool_trajectory(
    *,
    expected: list[str],
    actual: list[str],
    max_calls: int,
) -> EvaluationScore:
    expected_counts = Counter(expected)
    actual_counts = Counter(actual)
    expected_present = all(actual_counts[name] >= count for name, count in expected_counts.items())
    bounded = len(actual) <= max_calls
    unexpected = [name for name in actual_counts if name not in expected_counts]
    return EvaluationScore(
        passed=expected_present and bounded and not unexpected,
        details={
            "expected": expected,
            "actual": actual,
            "call_count": len(actual),
            "max_calls": max_calls,
            "unexpected": unexpected,
        },
    )


def evaluate_retrieval(
    *,
    expected_document_ids: list[str],
    actual: RagResult,
    expected_fallback: bool | None = None,
) -> EvaluationScore:
    actual_ids = [
        document.source.document_id
        for document in actual.documents
        if document.source.document_id
    ]
    sources_match = all(document_id in actual_ids for document_id in expected_document_ids)
    fallback_matches = (
        expected_fallback is None or actual.fallback_required == expected_fallback
    )
    return EvaluationScore(
        passed=sources_match and fallback_matches,
        details={
            "expected_document_ids": expected_document_ids,
            "actual_document_ids": actual_ids,
            "expected_fallback": expected_fallback,
            "actual_fallback": actual.fallback_required,
        },
    )
