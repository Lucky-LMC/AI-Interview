import json

from backend.graph.runtime.contracts import (
    ExecutionError,
    ExecutionTrace,
    SourceRef,
    ToolResult,
    WorkflowRuntime,
)
from backend.graph.runtime.errors import (
    ErrorCategory,
    MissingConfigurationError,
    classify_exception,
)


def test_tool_result_is_json_serializable():
    result = ToolResult.success(
        data={"items": [1]},
        sources=[SourceRef(title="STAR 法则", document_id="kb-star")],
    )

    payload = result.model_dump(mode="json")

    assert payload["ok"] is True
    assert payload["sources"][0]["document_id"] == "kb-star"
    json.dumps(payload, ensure_ascii=False)


def test_workflow_runtime_is_checkpoint_serializable():
    runtime = WorkflowRuntime.new(run_id="run-1", workflow_version="2.0")
    runtime.current_node = "interviewer_agent"
    runtime.errors.append(
        ExecutionError(
            component="interviewer_agent",
            code="MODEL_TIMEOUT",
            category=ErrorCategory.TRANSIENT,
            retryable=True,
        )
    )
    runtime.traces.append(
        ExecutionTrace(event="node_start", component="interviewer_agent")
    )

    payload = runtime.model_dump(mode="json")

    assert payload["run_id"] == "run-1"
    assert payload["errors"][0]["category"] == "transient"
    json.dumps(payload, ensure_ascii=False)


def test_timeout_is_transient():
    assert classify_exception(TimeoutError()) is ErrorCategory.TRANSIENT


def test_invalid_input_is_validation_error():
    assert classify_exception(ValueError("bad input")) is ErrorCategory.VALIDATION


def test_missing_config_is_permanent():
    error = MissingConfigurationError("TAVILY_API_KEY")

    assert classify_exception(error) is ErrorCategory.PERMANENT
    assert "TAVILY_API_KEY" not in error.public_message
