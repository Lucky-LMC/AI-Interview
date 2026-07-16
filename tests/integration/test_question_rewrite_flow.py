from importlib import import_module

from backend.graph.nodes.review_question_node import review_question_node


def _state(question: str, retry_count: int = 0):
    return {
        "round": 2,
        "max_rounds": 3,
        "target_position": "AI应用开发工程师",
        "resume_text": "### 项目经历亮点\n- WorkMind：使用 LangGraph 和 RAG",
        "history": [{"question": question, "answer": ""}],
        "question_retry_count": retry_count,
        "question_rewrite_instruction": "",
        "question_review": {},
    }


def test_second_quality_failure_uses_deterministic_fallback(monkeypatch):
    module = import_module("backend.graph.nodes.review_question_node")

    def reject(*_args, **_kwargs):
        from backend.models.schemas import QuestionReviewResult

        return QuestionReviewResult(
            passed=False,
            score=0.2,
            issues=["质量不足"],
            rewrite_instruction="重写",
            decision_source="rules",
        )

    monkeypatch.setattr(module, "evaluate_question", reject)
    result = review_question_node(_state("什么是RAG？", retry_count=1))

    assert result["question_review"]["used_fallback"] is True
    assert result["question_review"]["passed"] is True
    assert "项目" in result["history"][-1]["question"]


def test_first_quality_failure_requests_exactly_one_rewrite(monkeypatch):
    module = import_module("backend.graph.nodes.review_question_node")

    def reject(*_args, **_kwargs):
        from backend.models.schemas import QuestionReviewResult

        return QuestionReviewResult(
            passed=False,
            score=0.4,
            issues=["缺少简历证据"],
            rewrite_instruction="结合具体项目重写",
            decision_source="judge",
        )

    monkeypatch.setattr(module, "evaluate_question", reject)
    result = review_question_node(_state("什么是RAG？"))

    assert result["question_retry_count"] == 1
    assert result["question_review"]["passed"] is False
    assert result["question_rewrite_instruction"] == "结合具体项目重写"
