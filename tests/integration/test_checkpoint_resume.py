import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from backend.graph.runtime.contracts import WorkflowRuntime
from backend.graph.workflow.interview_workflow import create_interview_graph


@pytest.mark.asyncio
async def test_async_checkpoint_resumes_after_human_answer():
    async def interviewer(state):
        updated = state.copy()
        updated["round"] = state.get("round", 0) + 1
        updated["history"] = [
            *state.get("history", []),
            {
                "question": "你在WorkMind项目中如何设计LangGraph工作流及其容错机制？",
                "answer": "",
            },
        ]
        return updated

    async def feedback(state):
        return {**state, "learning_resources": "- LangGraph 官方文档"}

    async def report(state):
        return {**state, "report": "# 面试报告\n流程完成"}

    saver = InMemorySaver()
    graph = create_interview_graph(
        checkpointer=saver,
        node_overrides={
            "interviewer_agent": interviewer,
            "feedback_agent": feedback,
            "generate_report": report,
        },
    )
    config = {"configurable": {"thread_id": "checkpoint-resume"}}
    initial = {
        "round": 0,
        "max_rounds": 1,
        "resume_path": "unused.pdf",
        "resume_text": (
            "### 目标岗位\nAI应用开发工程师\n### 核心技能\nLangGraph\n"
            "### 项目经历亮点\n- WorkMind：工作流\n### 面试关注点\n容错"
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
        "runtime": WorkflowRuntime.new(run_id="checkpoint-resume", workflow_version="2.0"),
    }

    started = await graph.ainvoke(initial, config)
    assert started["history"][-1]["answer"] == ""

    current = await graph.aget_state(config)
    history = current.values["history"]
    history[-1]["answer"] = "通过分层状态和 RetryPolicy 实现。"
    await graph.aupdate_state(config, {"history": history})
    finished = await graph.ainvoke(None, config)

    assert finished["is_finished"] is True
    assert finished["report"].startswith("# 面试报告")


@pytest.mark.asyncio
async def test_runtime_contract_round_trips_through_async_sqlite(tmp_path):
    checkpoint_path = tmp_path / "checkpoint.sqlite"
    config = {"configurable": {"thread_id": "sqlite-roundtrip"}}
    state = {
        "round": 0,
        "max_rounds": 1,
        "resume_path": "",
        "resume_text": "",
        "target_position": "",
        "resume_validation": {},
        "resume_valid": False,
        "history": [],
        "question_review": {},
        "question_retry_count": 0,
        "question_rewrite_instruction": "",
        "learning_resources": "",
        "report": "",
        "is_finished": False,
        "runtime": WorkflowRuntime.new(run_id="sqlite-roundtrip", workflow_version="2.0"),
    }

    async with AsyncSqliteSaver.from_conn_string(str(checkpoint_path)) as saver:
        await saver.setup()
        graph = create_interview_graph(checkpointer=saver)
        await graph.ainvoke(state, config)
        restored = await graph.aget_state(config)

    assert restored.values["runtime"].run_id == "sqlite-roundtrip"
