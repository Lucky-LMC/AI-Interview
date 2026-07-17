import json
from importlib import import_module

import backend.config as config

consultant_tools = import_module("backend.graph.tools.consultant_tools")
feedback_tools = import_module("backend.graph.tools.feedback_tools")
interviewer_tools = import_module("backend.graph.tools.interviewer_tools")


def _payload(tool, arguments):
    return json.loads(tool.invoke(arguments))


def test_interviewer_tavily_missing_key_is_permanent(monkeypatch):
    monkeypatch.setattr(config, "TAVILY_API_KEY", "")

    result = _payload(
        interviewer_tools.search_interview_questions,
        {"topic": "LangGraph"},
    )

    assert result["ok"] is False
    assert result["error_code"] == "INTERVIEW_SEARCH_NOT_CONFIGURED"
    assert result["retryable"] is False


def test_feedback_tavily_missing_key_is_permanent(monkeypatch):
    monkeypatch.setattr(config, "TAVILY_API_KEY", "")

    result = _payload(
        feedback_tools.search_learning_resources,
        {"topic": "Redis"},
    )

    assert result["error_code"] == "LEARNING_RESOURCE_SEARCH_NOT_CONFIGURED"
    assert result["retryable"] is False


def test_consultant_tavily_missing_key_is_permanent(monkeypatch):
    monkeypatch.setattr(consultant_tools, "TAVILY_API_KEY", "")

    result = _payload(consultant_tools.tavily_search, {"query": "AI 面试"})

    assert result["error_code"] == "TAVILY_NOT_CONFIGURED"
    assert result["retryable"] is False
