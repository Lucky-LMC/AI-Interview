"""Helpers for appending bounded, serializable execution traces."""

from typing import Any

from .contracts import ExecutionTrace, WorkflowRuntime


MAX_TRACES = 200


def append_trace(
    runtime: WorkflowRuntime,
    *,
    event: str,
    component: str,
    metadata: dict[str, Any] | None = None,
) -> WorkflowRuntime:
    """Append a safe trace and cap checkpoint growth."""

    runtime.traces.append(
        ExecutionTrace(
            event=event,
            component=component,
            metadata=metadata or {},
        )
    )
    if len(runtime.traces) > MAX_TRACES:
        runtime.traces = runtime.traces[-MAX_TRACES:]
    return runtime
