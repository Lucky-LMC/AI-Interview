import pytest
from langgraph.checkpoint.memory import InMemorySaver

from backend.graph.runtime.contracts import WorkflowRuntime
from backend.graph.workflow.interview_workflow import create_interview_graph


@pytest.mark.asyncio
async def test_two_round_offline_flow_reaches_report():
    async def interviewer(state):
        round_num = state.get("round", 0) + 1
        question = (
            "你在WorkMind项目中如何设计LangGraph工作流的状态边界与错误处理？"
            if round_num == 1
            else "你在WorkMind项目中如何优化LangGraph工作流，并权衡重试与降级策略？"
        )
        return {
            **state,
            "round": round_num,
            "history": [*state.get("history", []), {"question": question, "answer": ""}],
        }

    async def feedback(state):
        return {**state, "learning_resources": "- LangGraph 官方文档"}

    async def report(state):
        return {**state, "report": "# 面试报告\n\n完成两轮离线流程。"}

    graph = create_interview_graph(
        checkpointer=InMemorySaver(),
        node_overrides={
            "interviewer_agent": interviewer,
            "feedback_agent": feedback,
            "generate_report": report,
        },
    )
    config = {"configurable": {"thread_id": "full-offline"}, "recursion_limit": 30}
    state = {
        "round": 0,
        "max_rounds": 2,
        "resume_path": "unused.pdf",
        "resume_text": (
            "### 目标岗位\nAI应用开发工程师\n### 核心技能\nLangGraph\n"
            "### 项目经历亮点\n- WorkMind：Agent 工作流\n### 面试关注点\n容错"
        ),
        "target_position": "AI应用开发工程师",
        "resume_validation": {},
        "resume_valid": False,
        "history": [],
        "question_review": {},
        "question_retry_count": 0,
        "question_rewrite_instruction": "",
        "learning_resources": "",
        "report": "",
        "is_finished": False,
        "runtime": WorkflowRuntime.new(run_id="full-offline", workflow_version="2.0"),
    }

    result = await graph.ainvoke(state, config)
    for answer in ("第一轮回答", "第二轮回答"):
        current = await graph.aget_state(config)
        history = current.values["history"]
        history[-1]["answer"] = answer
        await graph.aupdate_state(config, {"history": history})
        result = await graph.ainvoke(None, config)

    assert result["is_finished"] is True
    assert len(result["history"]) == 2
    assert result["report"].startswith("# 面试报告")
