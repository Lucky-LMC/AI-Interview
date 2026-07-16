from importlib import import_module

from backend.graph.runtime.policies import AgentPolicy
from backend.models.schemas import FeedbackRecommendations, InterviewQuestion


def test_interviewer_policy_has_bounded_calls():
    policy = AgentPolicy.interviewer()

    assert policy.model_run_limit == 4
    assert policy.global_tool_run_limit == 1
    assert policy.tool_limits["search_interview_questions"] == 1


def test_feedback_policy_allows_bounded_resource_searches():
    policy = AgentPolicy.feedback()

    assert policy.model_run_limit == 6
    assert policy.tool_limits["search_learning_resources"] == 3


def test_consultant_policy_bounds_rag_and_web_fallback():
    policy = AgentPolicy.consultant()

    assert policy.tool_limits == {"search_knowledge_base": 1, "tavily_search": 1}
    assert policy.global_tool_run_limit == 2


def test_interviewer_factory_uses_create_agent_and_structured_output(monkeypatch):
    module = import_module("backend.graph.agents.interviewer_agent")
    captured = {}

    def fake_create_agent(**kwargs):
        captured.update(kwargs)
        return "compiled-interviewer"

    monkeypatch.setattr(module, "create_agent", fake_create_agent)
    result = module.create_interviewer_agent(model=object())

    assert result == "compiled-interviewer"
    assert captured["response_format"] is InterviewQuestion
    assert captured["name"] == "interviewer_agent"
    assert captured["middleware"]


def test_feedback_factory_uses_structured_output(monkeypatch):
    module = import_module("backend.graph.agents.feedback_agent")
    captured = {}

    def fake_create_agent(**kwargs):
        captured.update(kwargs)
        return "compiled-feedback"

    monkeypatch.setattr(module, "create_agent", fake_create_agent)
    result = module.create_feedback_agent(model=object())

    assert result == "compiled-feedback"
    assert captured["response_format"] is FeedbackRecommendations


def test_consultant_factory_keeps_free_text_response(monkeypatch):
    module = import_module("backend.graph.agents.consultant_agent")
    captured = {}

    def fake_create_agent(**kwargs):
        captured.update(kwargs)
        return "compiled-consultant"

    monkeypatch.setattr(module, "create_agent", fake_create_agent)
    result = module.create_consultant_agent(model=object())

    assert result == "compiled-consultant"
    assert "response_format" not in captured
    assert captured["name"] == "consultant_agent"
