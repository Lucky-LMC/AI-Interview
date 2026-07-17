import uuid

import pytest


pytestmark = pytest.mark.integration


def test_graph_contains_expected_nodes(compiled_graph):
    assert set(compiled_graph.get_graph().nodes) >= {
        "parse_resume",
        "validate_resume",
        "interviewer_agent",
        "review_question",
        "answer",
        "check_finish",
        "feedback_agent",
        "generate_report",
    }


@pytest.mark.asyncio
async def test_invalid_resume_ends_before_question(compiled_graph, invalid_interview_state):
    config = {"configurable": {"thread_id": f"test-{uuid.uuid4()}"}}

    result = await compiled_graph.ainvoke(invalid_interview_state, config)

    assert result["resume_valid"] is False
    assert result["history"] == []
