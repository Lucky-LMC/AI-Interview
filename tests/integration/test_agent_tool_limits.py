from langchain.agents.middleware import ModelCallLimitMiddleware, ToolCallLimitMiddleware

from backend.graph.runtime.middleware import build_agent_middleware
from backend.graph.runtime.policies import AgentPolicy


def test_interviewer_middleware_contains_enforced_run_limits():
    middleware = build_agent_middleware(AgentPolicy.interviewer())

    model_limits = [item for item in middleware if isinstance(item, ModelCallLimitMiddleware)]
    tool_limits = [item for item in middleware if isinstance(item, ToolCallLimitMiddleware)]

    assert [item.run_limit for item in model_limits] == [4]
    assert any(item.tool_name is None and item.run_limit == 1 for item in tool_limits)
    assert any(
        item.tool_name == "search_interview_questions" and item.run_limit == 1
        for item in tool_limits
    )


def test_consultant_middleware_has_no_unbounded_tool_path():
    middleware = build_agent_middleware(AgentPolicy.consultant())
    tool_limits = [item for item in middleware if isinstance(item, ToolCallLimitMiddleware)]

    limits = {item.tool_name: item.run_limit for item in tool_limits}

    assert limits[None] == 2
    assert limits["search_knowledge_base"] == 1
    assert limits["tavily_search"] == 1
