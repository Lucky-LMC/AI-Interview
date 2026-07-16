import inspect


def test_required_langchain_capabilities_import():
    from langchain.agents import create_agent
    from langchain.agents.middleware import (
        ModelCallLimitMiddleware,
        ModelRetryMiddleware,
        ToolCallLimitMiddleware,
        ToolRetryMiddleware,
    )

    assert callable(create_agent)
    assert all(
        middleware is not None
        for middleware in (
            ModelCallLimitMiddleware,
            ModelRetryMiddleware,
            ToolCallLimitMiddleware,
            ToolRetryMiddleware,
        )
    )


def test_required_langgraph_capabilities_import():
    from langgraph.errors import NodeError
    from langgraph.types import RetryPolicy, TimeoutPolicy

    assert RetryPolicy is not None
    assert TimeoutPolicy is not None
    assert NodeError is not None


def test_state_graph_supports_node_error_handlers():
    from langgraph.graph import StateGraph

    parameters = inspect.signature(StateGraph.add_node).parameters

    assert "retry_policy" in parameters
    assert "cache_policy" in parameters
    assert "defer" in parameters
    assert "error_handler" in parameters
    assert "timeout" in parameters
