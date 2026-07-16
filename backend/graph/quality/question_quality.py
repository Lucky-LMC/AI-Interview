"""Layered question quality: rules, semantic judge, deterministic fallback."""

import re
from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.graph.llm import openai_llm
from backend.models.schemas import QuestionReviewDimension, QuestionReviewResult


class RuleQualityResult(BaseModel):
    route: Literal["approve", "judge", "rewrite"]
    score: float = Field(ge=0.0, le=1.0)
    dimensions: list[QuestionReviewDimension] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


Judge = Callable[[str, dict[str, Any], RuleQualityResult], QuestionReviewResult]

APPROVE_THRESHOLD = 0.85
REWRITE_THRESHOLD = 0.55


def _dimension(name: str, score: float, reason: str) -> QuestionReviewDimension:
    return QuestionReviewDimension(name=name, score=score, reason=reason)


def _extract_resume_evidence(resume_text: str) -> list[str]:
    known = [
        "Redis", "MySQL", "Spring", "FastAPI", "LangGraph", "LangChain",
        "Python", "Java", "RAG", "Agent", "WorkMind", "Docker",
    ]
    evidence = [token for token in known if token.lower() in resume_text.lower()]
    project_names = re.findall(r"[-：:]\s*([A-Za-z][A-Za-z0-9_-]{2,30})", resume_text)
    return list(dict.fromkeys([*evidence, *project_names]))


def _normalized_overlap(left: str, right: str) -> float:
    left_chars = set(re.sub(r"\s+", "", left))
    right_chars = set(re.sub(r"\s+", "", right))
    if not left_chars or not right_chars:
        return 0.0
    return len(left_chars & right_chars) / len(left_chars | right_chars)


def score_question_rules(question: str, state: dict[str, Any]) -> RuleQualityResult:
    """Fast, deterministic checks that avoid unnecessary judge calls."""

    normalized = question.strip()
    format_ok = 6 <= len(normalized) <= 220 and (
        "?" in normalized or "？" in normalized or normalized.endswith(("吗", "呢"))
    )
    format_score = 1.0 if format_ok else 0.0

    evidence_tokens = _extract_resume_evidence(state.get("resume_text", ""))
    evidence_hits = [token for token in evidence_tokens if token.lower() in normalized.lower()]
    project_context = any(marker in normalized for marker in ("项目", "经历", "负责"))
    evidence_score = 1.0 if evidence_hits and project_context else 0.65 if evidence_hits else 0.2

    history = state.get("history", [])
    previous_questions = [item.get("question", "") for item in history[:-1]]
    duplicated = any(_normalized_overlap(normalized, previous) > 0.75 for previous in previous_questions)
    duplicate_score = 0.0 if duplicated else 1.0

    round_num = state.get("round", 1)
    markers = (
        ["沟通", "协作", "冲突", "复盘", "规划", "取舍"]
        if round_num >= 3
        else ["原理", "实现", "设计", "架构", "优化", "排查", "权衡", "难点"]
    )
    difficulty_score = 1.0 if any(marker in normalized for marker in markers) else 0.35

    dimensions = [
        _dimension("format", format_score, "问题长度、问句格式和可回答性"),
        _dimension("resume_evidence", evidence_score, "问题是否引用简历中的项目或技术证据"),
        _dimension("duplicate_risk", duplicate_score, "问题是否与历史问题高度重复"),
        _dimension("round_difficulty", difficulty_score, "问题是否符合当前轮次的深度要求"),
    ]
    score = sum(item.score for item in dimensions) / len(dimensions)
    issues = [item.reason for item in dimensions if item.score < 0.55]
    route = "approve" if score >= APPROVE_THRESHOLD and not issues else (
        "rewrite" if score < REWRITE_THRESHOLD else "judge"
    )
    return RuleQualityResult(route=route, score=score, dimensions=dimensions, issues=issues)


def _rewrite_instruction(issues: list[str], state: dict[str, Any]) -> str:
    target = state.get("target_position", "目标岗位")
    issue_text = "；".join(issues) if issues else "问题缺少项目深度或明确证据"
    return (
        f"请围绕{target}和候选人的具体项目重写当前轮问题："
        "必须引用简历中的项目或技术，避免概念背诵，不重复历史问题，并要求说明实现、难点或权衡。"
        f"需修复：{issue_text}"
    )


def _default_judge(
    question: str,
    state: dict[str, Any],
    rules: RuleQualityResult,
) -> QuestionReviewResult:
    judge = openai_llm.bind(temperature=0).with_structured_output(QuestionReviewResult)
    prompt = f"""你是面试问题质量审核器，只评审问题，不回答问题。

候选岗位：{state.get('target_position', '未知岗位')}
当前轮次：{state.get('round', 1)}
简历摘要：
{state.get('resume_text', '')}

待审核问题：{question}
规则初评分：{rules.score:.2f}

判断问题是否具体引用简历证据、技术正确、难度适合、清晰且不重复。
不合格时给出可执行的 rewrite_instruction。"""
    result = judge.invoke(prompt)
    result.decision_source = "judge"
    return result


def evaluate_question(
    question: str,
    state: dict[str, Any],
    *,
    judge: Judge | None = None,
) -> QuestionReviewResult:
    rules = score_question_rules(question, state)
    if rules.route == "approve":
        return QuestionReviewResult(
            passed=True,
            score=rules.score,
            dimensions=rules.dimensions,
            issues=[],
            rewrite_instruction="",
            decision_source="rules",
        )
    if rules.route == "rewrite":
        return QuestionReviewResult(
            passed=False,
            score=rules.score,
            dimensions=rules.dimensions,
            issues=rules.issues,
            rewrite_instruction=_rewrite_instruction(rules.issues, state),
            decision_source="rules",
        )

    judge_fn = judge or _default_judge
    try:
        result = judge_fn(question, state, rules)
    except Exception:
        return QuestionReviewResult(
            passed=False,
            score=rules.score,
            dimensions=rules.dimensions,
            issues=["语义审核暂时不可用，按保守策略重写"],
            rewrite_instruction=_rewrite_instruction(rules.issues, state),
            decision_source="judge_fallback",
        )
    if result is None:
        raise ValueError("question judge returned no result")
    result.decision_source = "judge"
    if not result.passed and not result.rewrite_instruction:
        result.rewrite_instruction = _rewrite_instruction(result.issues, state)
    return result


def fallback_question(state: dict[str, Any]) -> str:
    target = state.get("target_position", "目标岗位")
    round_num = state.get("round", 1)
    if round_num == 1:
        return f"请结合简历中的一个项目，说明完成{target}工作所需的核心技术，以及你具体如何应用它？"
    if round_num == 2:
        return "请选择简历中最有代表性的项目，说明你负责的模块、遇到的技术难点、解决方案及关键权衡？"
    return "请复盘一次项目协作中的困难，说明你的处理方式、结果，以及如果重来会如何改进？"
