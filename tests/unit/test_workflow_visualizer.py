from backend.graph.agents.consultant_agent import consultant_agent
from backend.graph.workflow import create_interview_graph
from backend.utils.workflow_visualizer import _graph_to_dot


def test_workflow_visualizer_expands_real_create_agent_subgraphs():
    compiled_graph = create_interview_graph()

    dot = _graph_to_dot(compiled_graph.get_graph(xray=True))

    assert "interviewer_agent / create_agent" in dot
    assert "feedback_agent / create_agent" in dot
    assert "Middleware hooks (collapsed)" in dot
    assert "ModelCallLimitMiddleware" in dot
    assert "ToolCallLimitMiddleware" in dot
    assert "ModelCallLimitMiddleware.before_model" not in dot
    assert "model" in dot
    assert "tools" in dot


def test_consultant_visualizer_uses_real_compiled_agent_graph():
    dot = _graph_to_dot(
        consultant_agent.get_graph(xray=True),
        root_agent_name="consultant_agent",
    )

    assert "consultant_agent / create_agent" in dot
    assert "Middleware hooks (collapsed)" in dot
    assert "model" in dot
    assert "tools" in dot


def test_debug_projection_can_keep_raw_middleware_hooks():
    dot = _graph_to_dot(
        create_interview_graph().get_graph(xray=True),
        collapse_middleware=False,
    )

    assert "ModelCallLimitMiddleware.before_model" in dot
