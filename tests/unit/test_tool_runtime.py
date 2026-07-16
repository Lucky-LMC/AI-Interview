from backend.graph.runtime.tool_runtime import timed_tool_call


def test_timeout_is_retryable():
    def fail():
        raise TimeoutError("provider timed out with internal details")

    result = timed_tool_call("search", fail)

    assert result.ok is False
    assert result.retryable is True
    assert result.error_code == "SEARCH_TIMEOUT"
    assert "internal details" not in result.model_dump_json()


def test_missing_configuration_is_not_retried():
    called = False

    def should_not_run():
        nonlocal called
        called = True

    result = timed_tool_call(
        "tavily",
        should_not_run,
        missing_config="TAVILY_API_KEY",
    )

    assert result.ok is False
    assert result.retryable is False
    assert result.error_code == "TAVILY_NOT_CONFIGURED"
    assert called is False


def test_success_records_latency_and_data():
    result = timed_tool_call("knowledge_base", lambda: {"items": ["STAR"]})

    assert result.ok is True
    assert result.data == {"items": ["STAR"]}
    assert result.latency_ms >= 0
