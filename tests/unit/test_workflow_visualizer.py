from backend.graph.agents.consultant_agent import consultant_agent
from backend.graph.workflow import create_interview_graph
from backend.utils.workflow_visualizer import _graph_to_dot


def test_workflow_visualizer_expands_real_create_agent_subgraphs():
    compiled_graph = create_interview_graph()

    dot = _graph_to_dot(compiled_graph.get_graph(xray=True))

    assert "interviewer_agent / create_agent" in dot
    assert "feedback_agent / create_agent" in dot
    assert "ModelCallLimitMiddleware.before_model" in dot
    assert "search_interview_questions" in dot
    assert "search_learning_resources" in dot


def test_consultant_visualizer_uses_real_compiled_agent_graph():
    dot = _graph_to_dot(
        consultant_agent.get_graph(xray=True),
        root_agent_name="consultant_agent",
    )

    assert "consultant_agent / create_agent" in dot
    assert "search_knowledge_base" in dot
    assert "tavily_search" in dot
