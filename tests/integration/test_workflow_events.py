import json

from backend.graph.runtime.tracing import public_tool_events


def test_tool_start_event_exposes_name_without_arguments():
    events = public_tool_events({
        "event": "on_tool_start",
        "name": "search_knowledge_base",
        "data": {"input": {"query": "private user question"}},
    })

    assert events == [{"type": "tool_start", "tool": "search_knowledge_base"}]
    assert "private user question" not in json.dumps(events)


def test_degraded_tool_result_is_visible_without_raw_payload():
    tool_result = {
        "ok": True,
        "data": {"documents": [], "fallback_required": True},
        "retryable": False,
        "sources": [],
        "latency_ms": 12,
        "degraded": True,
    }
    events = public_tool_events({
        "event": "on_tool_end",
        "name": "search_knowledge_base",
        "data": {"output": json.dumps(tool_result)},
    })

    assert events[0] == {
        "type": "tool_end",
        "tool": "search_knowledge_base",
        "ok": True,
        "latency_ms": 12,
        "source_count": 0,
    }
    assert events[1]["type"] == "degraded"
    assert "documents" not in json.dumps(events)
