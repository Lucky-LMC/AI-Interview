from backend.evaluation.evaluators import (
    evaluate_retrieval,
    evaluate_tool_trajectory,
)
from backend.graph.rag.service import RagResult, RetrievedChunk
from backend.graph.runtime.contracts import SourceRef


def test_tool_trajectory_evaluator_rejects_extra_calls():
    score = evaluate_tool_trajectory(
        expected=["search_interview_questions"],
        actual=["search_interview_questions", "search_interview_questions"],
        max_calls=1,
    )

    assert score.passed is False
    assert "call_count" in score.details


def test_tool_trajectory_accepts_expected_bounded_call():
    score = evaluate_tool_trajectory(
        expected=["search_knowledge_base"],
        actual=["search_knowledge_base"],
        max_calls=2,
    )

    assert score.passed is True


def test_rag_evaluator_checks_expected_source():
    result = RagResult(
        query="STAR",
        confidence="high",
        fallback_required=False,
        documents=[
            RetrievedChunk(
                content="STAR 法则",
                content_hash="hash",
                source=SourceRef(title="STAR", document_id="kb-star", score=0.2),
            )
        ],
    )

    score = evaluate_retrieval(expected_document_ids=["kb-star"], actual=result)

    assert score.passed is True


def test_rag_evaluator_rejects_missing_source():
    result = RagResult(
        query="STAR",
        confidence="low",
        fallback_required=True,
        documents=[],
    )

    score = evaluate_retrieval(expected_document_ids=["kb-star"], actual=result)

    assert score.passed is False
