# AI智能面试辅助系统V1.0，作者刘梦畅
"""
面试问题质量审查节点
"""
from backend.graph.state import InterviewState
from backend.models.schemas import QuestionReviewDimension, QuestionReviewResult


MIN_PASS_SCORE = 0.70


def _score_relevance(question: str, resume_text: str, target_position: str) -> QuestionReviewDimension:
    signals = 0
    if target_position and target_position not in {"未知岗位", "未识别"} and target_position in question:
        signals += 1
    if "项目" in question or "简历" in question:
        signals += 1
    if any(token and token in question for token in _extract_resume_tokens(resume_text)):
        signals += 1

    if signals >= 3:
        score = 1.0
    elif signals == 2:
        score = 0.80
    elif signals == 1:
        score = 0.60
    else:
        score = 0.30
    return QuestionReviewDimension(
        name="relevance",
        score=score,
        reason="检查问题是否结合目标岗位、简历或项目经历",
    )


def _score_difficulty(question: str, round_num: int) -> QuestionReviewDimension:
    technical_markers = ["原理", "实现", "架构", "优化", "设计", "排查", "权衡", "项目"]
    soft_markers = ["沟通", "协作", "规划", "冲突", "复盘", "优势", "不足"]
    markers = soft_markers if round_num >= 3 else technical_markers
    score = 1.0 if any(marker in question for marker in markers) else 0.55
    return QuestionReviewDimension(
        name="difficulty",
        score=score,
        reason="检查问题是否符合当前轮次的考察重点",
    )


def _score_duplicate(question: str, history: list[dict[str, str]]) -> QuestionReviewDimension:
    previous_questions = [item.get("question", "") for item in history[:-1]]
    duplicated = any(_normalized_overlap(question, previous) > 0.75 for previous in previous_questions)
    score = 0.0 if duplicated else 1.0
    return QuestionReviewDimension(
        name="duplicate_risk",
        score=score,
        reason="检查是否与历史问题高度重复",
    )


def _score_clarity(question: str) -> QuestionReviewDimension:
    length_ok = 8 <= len(question.strip()) <= 220
    asks_question = "?" in question or "？" in question or question.strip().endswith(("吗", "呢"))
    score = 1.0 if length_ok and asks_question else 0.55
    return QuestionReviewDimension(
        name="clarity",
        score=score,
        reason="检查问题是否具体、清晰、可回答",
    )


def _extract_resume_tokens(resume_text: str) -> list[str]:
    tokens = []
    for marker in ["Redis", "MySQL", "Spring", "FastAPI", "LangGraph", "Python", "Java", "RAG", "Agent"]:
        if marker in resume_text:
            tokens.append(marker)
    return tokens


def _normalized_overlap(left: str, right: str) -> float:
    left_chars = set(left.strip())
    right_chars = set(right.strip())
    if not left_chars or not right_chars:
        return 0.0
    return len(left_chars & right_chars) / len(left_chars | right_chars)


def _fallback_question(state: InterviewState) -> str:
    target_position = state.get("target_position", "目标岗位")
    round_num = state.get("round", 1)
    if round_num == 1:
        return f"请结合你的简历，说明你做{target_position}最核心的技术基础是什么？请举一个项目中的实际例子。"
    if round_num == 2:
        return "请选择简历中最有代表性的一个项目，说明你负责的核心模块、遇到的技术难点，以及你是如何解决的？"
    return "请复盘一次你在项目协作中遇到的困难，说明你的处理方式、结果，以及如果重来会如何改进？"


def _build_rewrite_instruction(issues: list[str], state: InterviewState) -> str:
    target_position = state.get("target_position", "目标岗位")
    return (
        f"请围绕{target_position}和候选人简历重写当前轮问题，要求："
        "1. 必须指向具体项目或技能；2. 不要重复历史问题；3. 问题要清晰可回答；"
        f"4. 修复这些问题：{'；'.join(issues)}"
    )


def review_question_node(state: InterviewState) -> InterviewState:
    """
    审查最新面试问题，失败时触发一次重写，再失败时使用模板兜底。
    """
    history = state.get("history", [])
    if not history:
        fallback = _fallback_question(state)
        result = QuestionReviewResult(
            passed=True,
            score=1.0,
            dimensions=[
                QuestionReviewDimension(name="fallback", score=1.0, reason="未生成问题时使用预置题型兜底"),
            ],
            issues=[],
            rewrite_instruction="",
            used_fallback=True,
        )
        new_state = state.copy()
        new_state["history"] = [{"question": fallback, "answer": ""}]
        new_state["question_review"] = result.model_dump()
        new_state["question_retry_count"] = 0
        new_state["question_rewrite_instruction"] = ""
        if not new_state.get("round"):
            new_state["round"] = 1
        return new_state

    question = history[-1].get("question", "")
    resume_text = state.get("resume_text", "")
    target_position = state.get("target_position", "未知岗位")
    round_num = state.get("round", 1)

    dimensions = [
        _score_relevance(question, resume_text, target_position),
        _score_difficulty(question, round_num),
        _score_duplicate(question, history),
        _score_clarity(question),
    ]
    score = sum(item.score for item in dimensions) / len(dimensions)
    issues = [item.reason for item in dimensions if item.score < MIN_PASS_SCORE]
    passed = score >= MIN_PASS_SCORE and not issues

    retry_count = state.get("question_retry_count", 0)
    new_state = state.copy()
    used_fallback = False

    if not passed and retry_count >= 1:
        fixed_history = history.copy()
        fixed_history[-1] = {"question": _fallback_question(state), "answer": ""}
        new_state["history"] = fixed_history
        passed = True
        used_fallback = True
        score = 1.0
        dimensions = [
            QuestionReviewDimension(name="fallback", score=1.0, reason="自动重写后仍未通过，已使用预置题型模板兜底"),
        ]
        issues = []

    rewrite_instruction = "" if passed else _build_rewrite_instruction(issues, state)
    result = QuestionReviewResult(
        passed=passed,
        score=score,
        dimensions=dimensions,
        issues=issues,
        rewrite_instruction=rewrite_instruction,
        used_fallback=used_fallback,
    )

    new_state["question_review"] = result.model_dump()
    new_state["question_rewrite_instruction"] = rewrite_instruction
    if not passed:
        new_state["question_retry_count"] = retry_count + 1
    else:
        new_state["question_retry_count"] = 0

    return new_state
