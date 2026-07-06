# AI智能面试辅助系统V1.0，作者刘梦畅
"""
简历结构化质量门禁节点
"""
from backend.graph.state import InterviewState
from backend.models.schemas import ResumeValidationResult


REQUIRED_RESUME_SECTIONS = {
    "target_position": "### 目标岗位",
    "skills": "### 核心技能",
    "projects": "### 项目经历亮点",
    "focus_points": "### 面试关注点",
}


def validate_resume_node(state: InterviewState) -> InterviewState:
    """
    校验 LLM 提取后的简历结构是否足够支撑后续面试提问。
    """
    resume_text = state.get("resume_text", "")
    target_position = state.get("target_position", "")
    issues = []

    if not resume_text.strip():
        issues.append("简历结构化摘要为空")

    if not target_position.strip() or target_position.strip() in {"未识别", "未提及"}:
        issues.append("目标岗位缺失或未识别")

    for section_name, marker in REQUIRED_RESUME_SECTIONS.items():
        if marker not in resume_text:
            issues.append(f"缺少必要简历结构: {section_name}")

    score = max(0.0, 1.0 - len(issues) * 0.25)
    passed = not issues
    rewrite_instruction = ""
    if issues:
        rewrite_instruction = "请补全目标岗位、核心技能、项目经历亮点和面试关注点后再生成高质量面试问题。"

    result = ResumeValidationResult(
        passed=passed,
        score=score,
        issues=issues,
        rewrite_instruction=rewrite_instruction,
    )

    new_state = state.copy()
    new_state["resume_validation"] = result.model_dump()
    new_state["resume_valid"] = result.passed
    return new_state
