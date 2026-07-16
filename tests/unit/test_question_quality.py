import pytest

from backend.graph.quality.question_quality import evaluate_question, score_question_rules
from backend.models.schemas import QuestionReviewResult


@pytest.fixture
def sample_state():
    return {
        "round": 2,
        "target_position": "AI应用开发工程师",
        "resume_text": "### 项目经历亮点\n- WorkMind：使用 Python、LangGraph 和 RAG 构建工作流",
        "history": [],
    }


def test_specific_project_question_is_approved_by_rules(sample_state):
    question = "你在WorkMind项目中为什么选择LangGraph设计工作流，遇到过什么权衡？"

    result = evaluate_question(question, sample_state, judge=lambda *_: None)

    assert result.passed is True
    assert result.decision_source == "rules"


def test_generic_definition_question_is_rewritten_by_borderline_judge(sample_state):
    calls = []

    def reject(question, state, rules):
        calls.append((question, rules.score))
        return QuestionReviewResult(
            passed=False,
            score=0.45,
            issues=["问题停留在概念定义，未结合项目决策"],
            rewrite_instruction="结合 WorkMind 项目的实际设计与权衡重写",
            decision_source="judge",
        )

    result = evaluate_question("什么是RAG？", sample_state, judge=reject)

    assert result.passed is False
    assert result.decision_source == "judge"
    assert len(calls) == 1


def test_obviously_invalid_question_skips_judge(sample_state):
    called = False

    def judge(*_):
        nonlocal called
        called = True

    result = evaluate_question("你好", sample_state, judge=judge)

    assert result.passed is False
    assert result.decision_source == "rules"
    assert called is False


def test_duplicate_question_is_detected(sample_state):
    question = "请说明你在WorkMind项目中如何设计LangGraph工作流？"
    sample_state["history"] = [
        {"question": question, "answer": "使用状态图"},
        {"question": question, "answer": ""},
    ]

    rules = score_question_rules(question, sample_state)

    duplicate = next(item for item in rules.dimensions if item.name == "duplicate_risk")
    assert duplicate.score == 0.0
