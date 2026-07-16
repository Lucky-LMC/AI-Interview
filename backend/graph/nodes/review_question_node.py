# AI智能面试辅助系统V1.0，作者刘梦畅
"""面试问题质量审查节点。"""

from backend.graph.quality.question_quality import evaluate_question, fallback_question
from backend.graph.state import InterviewState
from backend.models.schemas import QuestionReviewDimension, QuestionReviewResult


def review_question_node(state: InterviewState) -> InterviewState:
    """Apply rules, an optional semantic judge, one rewrite, then fallback."""

    history = state.get("history", [])
    if not history:
        history = [{"question": fallback_question(state), "answer": ""}]
        result = QuestionReviewResult(
            passed=True,
            score=1.0,
            dimensions=[
                QuestionReviewDimension(
                    name="fallback",
                    score=1.0,
                    reason="上游未生成问题，使用确定性模板",
                )
            ],
            used_fallback=True,
            decision_source="fallback",
        )
        new_state = state.copy()
        new_state.update(
            history=history,
            question_review=result.model_dump(),
            question_retry_count=0,
            question_rewrite_instruction="",
            round=state.get("round") or 1,
        )
        return new_state

    question = history[-1].get("question", "")
    result = evaluate_question(question, state)
    retry_count = state.get("question_retry_count", 0)
    new_state = state.copy()

    if not result.passed and retry_count >= 1:
        fixed_history = history.copy()
        fixed_history[-1] = {"question": fallback_question(state), "answer": ""}
        result = QuestionReviewResult(
            passed=True,
            score=1.0,
            dimensions=[
                QuestionReviewDimension(
                    name="fallback",
                    score=1.0,
                    reason="一次自动重写后仍未通过，使用确定性模板",
                )
            ],
            used_fallback=True,
            decision_source="fallback",
        )
        new_state["history"] = fixed_history

    new_state["question_review"] = result.model_dump()
    new_state["question_rewrite_instruction"] = result.rewrite_instruction
    new_state["question_retry_count"] = 0 if result.passed else retry_count + 1
    return new_state
