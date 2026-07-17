import asyncio

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from backend.graph.runtime.contracts import WorkflowRuntime
from backend.graph.workflow.interview_workflow import create_interview_graph


def _valid_state():
    return {
        "round": 0,
        "max_rounds": 1,
        "resume_path": "unused.pdf",
        "resume_text": (
            "### 目标岗位\nAI应用开发工程师\n"
            "### 核心技能\nLangGraph\n"
            "### 项目经历亮点\n- WorkMind：Agent 工作流\n"
            "### 面试关注点\n工作流容错"
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
        "runtime": WorkflowRuntime.new(run_id="fault-test", workflow_version="2.0"),
    }


@pytest.mark.asyncio
async def test_transient_interviewer_failure_retries_once():
    calls = 0

    async def flaky_interviewer(state):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise TimeoutError("temporary model timeout")
        updated = state.copy()
        updated["round"] = 1
        updated["history"] = [{
            "question": "你在WorkMind项目中如何设计LangGraph工作流的超时与重试机制？",
            "answer": "",
        }]
        return updated

    graph = create_interview_graph(
        checkpointer=InMemorySaver(),
        node_overrides={"interviewer_agent": flaky_interviewer},
    )
    result = await graph.ainvoke(
        _valid_state(),
        {"configurable": {"thread_id": "retry-once"}},
    )

    assert calls == 2
    assert result["question_review"]["passed"] is True


@pytest.mark.asyncio
async def test_interviewer_timeout_uses_safe_fallback():
    async def slow_interviewer(_state):
        await asyncio.sleep(0.05)

    graph = create_interview_graph(
        checkpointer=InMemorySaver(),
        node_overrides={"interviewer_agent": slow_interviewer},
        timeout_overrides={"interviewer_agent": 0.01},
    )
    result = await graph.ainvoke(
        _valid_state(),
        {"configurable": {"thread_id": "timeout-fallback"}},
    )

    assert "interviewer_agent" in result["runtime"].degraded_components
    assert result["history"][-1]["question"]
    assert result["question_review"]["passed"] is True
