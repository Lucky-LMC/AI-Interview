# AI智能面试辅助系统V1.0，作者刘梦畅
"""LangGraph orchestration with retries, async timeouts, and recovery."""

import sqlite3
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from backend.graph.nodes import (
    answer_node,
    ask_question_node,
    check_finish_node,
    feedback_node,
    generate_report_node,
    parse_resume_node,
    review_question_node,
    validate_resume_node,
)
from backend.graph.runtime.errors import ErrorCategory, classify_exception
from backend.graph.runtime.recovery import recover_node
from backend.graph.state import InterviewState


_project_root = Path(__file__).resolve().parents[3]
_checkpoint_db_path = _project_root / "checkpoints-sqlite" / "checkpoints.sqlite"
_checkpoint_db_path.parent.mkdir(parents=True, exist_ok=True)
_global_db_connection = sqlite3.connect(str(_checkpoint_db_path), check_same_thread=False)
_global_checkpointer = SqliteSaver(_global_db_connection)

NODE_TIMEOUTS = {
    "parse_resume": 45.0,
    "interviewer_agent": 60.0,
    "review_question": 30.0,
    "feedback_agent": 60.0,
    "generate_report": 60.0,
}


def _retry_transient(exc: Exception) -> bool:
    return classify_exception(exc) is ErrorCategory.TRANSIENT


def _retry_policy() -> RetryPolicy:
    return RetryPolicy(
        max_attempts=2,
        initial_interval=0.2,
        backoff_factor=2.0,
        max_interval=1.0,
        jitter=False,
        retry_on=_retry_transient,
    )


def create_interview_graph(
    *,
    checkpointer=None,
    node_overrides: dict[str, Callable[..., Any]] | None = None,
    timeout_overrides: dict[str, float] | None = None,
):
    """Compile the eight-node workflow with injectable test dependencies."""

    overrides = node_overrides or {}
    timeouts = {**NODE_TIMEOUTS, **(timeout_overrides or {})}
    nodes = {
        "parse_resume": parse_resume_node,
        "validate_resume": validate_resume_node,
        "interviewer_agent": ask_question_node,
        "review_question": review_question_node,
        "answer": answer_node,
        "check_finish": check_finish_node,
        "feedback_agent": feedback_node,
        "generate_report": generate_report_node,
        **overrides,
    }

    workflow = StateGraph(InterviewState)
    for name, action in nodes.items():
        if name in NODE_TIMEOUTS:
            workflow.add_node(
                name,
                action,
                retry_policy=_retry_policy(),
                timeout=timeouts[name],
                error_handler=recover_node,
            )
        else:
            workflow.add_node(name, action)

    workflow.add_edge(START, "parse_resume")
    workflow.add_edge("parse_resume", "validate_resume")
    workflow.add_conditional_edges(
        "validate_resume",
        lambda state: "valid" if state.get("resume_valid", False) else "invalid",
        {"valid": "interviewer_agent", "invalid": END},
    )
    workflow.add_edge("interviewer_agent", "review_question")
    workflow.add_conditional_edges(
        "review_question",
        lambda state: "approved" if state.get("question_review", {}).get("passed", False) else "rewrite",
        {"approved": "answer", "rewrite": "interviewer_agent"},
    )
    workflow.add_edge("answer", "check_finish")
    workflow.add_conditional_edges(
        "check_finish",
        lambda state: "finish" if state["is_finished"] else "continue",
        {"continue": "interviewer_agent", "finish": "feedback_agent"},
    )
    workflow.add_edge("feedback_agent", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile(
        checkpointer=checkpointer if checkpointer is not None else _global_checkpointer,
        interrupt_before=["answer"],
        name="interview_workflow_v2",
    )


@asynccontextmanager
async def interview_graph_session() -> AsyncIterator:
    """Open an async SQLite saver for one API request against the shared DB."""

    async with AsyncSqliteSaver.from_conn_string(str(_checkpoint_db_path)) as saver:
        await saver.setup()
        yield create_interview_graph(checkpointer=saver)
