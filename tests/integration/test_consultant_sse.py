from backend.graph.runtime.tracing import public_tool_events


def test_consultant_tool_lifecycle_sequence():
    raw_events = [
        {"event": "on_tool_start", "name": "search_knowledge_base", "data": {}},
        {
            "event": "on_tool_end",
            "name": "search_knowledge_base",
            "data": {"output": '{"ok":true,"latency_ms":4,"sources":[],"degraded":false}'},
        },
    ]

    events = [item for raw in raw_events for item in public_tool_events(raw)]

    assert [item["type"] for item in events] == ["tool_start", "tool_end"]
