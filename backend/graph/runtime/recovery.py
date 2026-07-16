"""Node-level recovery handlers for the outer LangGraph workflow."""

from uuid import uuid4

from langgraph.errors import NodeError
from langgraph.graph import END
from langgraph.types import Command

from backend.graph.quality.question_quality import fallback_question
from backend.models.schemas import QuestionReviewDimension, QuestionReviewResult

from .contracts import ExecutionError, WorkflowRuntime
from .errors import classify_exception


def _runtime_from(state: dict, node: str, error: BaseException) -> WorkflowRuntime:
    raw = state.get("runtime")
    if isinstance(raw, WorkflowRuntime):
        runtime = raw.model_copy(deep=True)
    elif isinstance(raw, dict):
        runtime = WorkflowRuntime.model_validate(raw)
    else:
        runtime = WorkflowRuntime.new(run_id=str(uuid4()), workflow_version="2.0")

    category = classify_exception(error)  # type: ignore[arg-type]
    runtime.current_node = node
    runtime.retry_counts[node] = runtime.retry_counts.get(node, 0) + 1
    if node not in runtime.degraded_components:
        runtime.degraded_components.append(node)
    runtime.errors.append(
        ExecutionError(
            component=node,
            code=f"{node.upper()}_FAILED",
            category=category,
            retryable=category.value == "transient",
        )
    )
    return runtime


async def recover_node(state: dict, error: NodeError) -> Command:
    """Return a safe state update so deterministic downstream edges can continue."""

    new_state = state.copy()
    new_state["runtime"] = _runtime_from(state, error.node, error.error)

    goto = END
    if error.node == "parse_resume":
        new_state.update(resume_text="", target_position="", resume_valid=False)
        goto = "validate_resume"
    elif error.node == "interviewer_agent":
        history = state.get("history", []).copy()
        entry = {"question": fallback_question(state), "answer": ""}
        retrying_question = (
            state.get("question_retry_count", 0) > 0
            and history
            and not history[-1].get("answer")
        )
        if retrying_question:
            history[-1] = entry
        else:
            history.append(entry)
            new_state["round"] = state.get("round", 0) + 1
        new_state["history"] = history
        new_state["question_review"] = QuestionReviewResult(
            passed=True,
            score=1.0,
            dimensions=[
                QuestionReviewDimension(
                    name="fallback",
                    score=1.0,
                    reason="面试官节点失败，使用已审核的确定性模板",
                )
            ],
            used_fallback=True,
            decision_source="fallback",
        ).model_dump()
        goto = "answer"
    elif error.node == "review_question":
        history = state.get("history", []).copy()
        entry = {"question": fallback_question(state), "answer": ""}
        if history:
            history[-1] = entry
        else:
            history.append(entry)
        new_state["history"] = history
        new_state["question_review"] = QuestionReviewResult(
            passed=True,
            score=1.0,
            dimensions=[
                QuestionReviewDimension(
                    name="fallback",
                    score=1.0,
                    reason="问题审核节点失败，使用确定性模板",
                )
            ],
            used_fallback=True,
            decision_source="fallback",
        ).model_dump()
        goto = "answer"
    elif error.node == "feedback_agent":
        new_state["learning_resources"] = "学习资源服务暂时不可用，请稍后重试。"
        goto = "generate_report"
    elif error.node == "generate_report":
        history = state.get("history", [])
        qa = "\n".join(
            f"- 问题：{item.get('question', '')}\n  回答：{item.get('answer', '')}"
            for item in history
        )
        new_state["report"] = f"# 面试报告（降级生成）\n\n## 面试记录\n{qa}"
    return Command(update=new_state, goto=goto)
