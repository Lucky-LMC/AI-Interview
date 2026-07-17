"""Helpers for appending bounded, serializable execution traces."""

from typing import Any
import json

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


def _tool_output_payload(output: Any) -> dict[str, Any]:
    if hasattr(output, "content"):
        output = output.content
    if isinstance(output, dict):
        return output
    if isinstance(output, str):
        try:
            parsed = json.loads(output)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def public_tool_events(event: dict[str, Any]) -> list[dict[str, Any]]:
    """Map LangChain events to public summaries without inputs or document text."""

    kind = event.get("event")
    tool_name = event.get("name", "unknown_tool")
    if kind == "on_tool_start":
        return [{"type": "tool_start", "tool": tool_name}]
    if kind != "on_tool_end":
        return []

    payload = _tool_output_payload(event.get("data", {}).get("output"))
    result = [{
        "type": "tool_end",
        "tool": tool_name,
        "ok": bool(payload.get("ok", True)),
        "latency_ms": int(payload.get("latency_ms", 0) or 0),
        "source_count": len(payload.get("sources", [])),
    }]
    if payload.get("degraded"):
        result.append({
            "type": "degraded",
            "component": tool_name,
            "error_code": payload.get("error_code"),
            "retryable": bool(payload.get("retryable", False)),
        })
    return result
