"""Serializable contracts shared across workflow checkpoints and tool calls."""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from .errors import ErrorCategory


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SourceRef(BaseModel):
    """Minimal provenance for retrieved or web content."""

    title: str
    url: str | None = None
    document_id: str | None = None
    section: str | None = None
    score: float | None = None


class ToolResult(BaseModel):
    """Normalized, safe response returned by every Agent tool."""

    ok: bool
    data: Any = None
    error_code: str | None = None
    retryable: bool = False
    sources: list[SourceRef] = Field(default_factory=list)
    latency_ms: int = Field(default=0, ge=0)
    degraded: bool = False

    @classmethod
    def success(
        cls,
        *,
        data: Any = None,
        sources: list[SourceRef] | None = None,
        latency_ms: int = 0,
        degraded: bool = False,
    ) -> "ToolResult":
        return cls(
            ok=True,
            data=data,
            sources=sources or [],
            latency_ms=latency_ms,
            degraded=degraded,
        )

    @classmethod
    def failure(
        cls,
        *,
        error_code: str,
        retryable: bool,
        latency_ms: int = 0,
        data: Any = None,
        sources: list[SourceRef] | None = None,
        degraded: bool = True,
    ) -> "ToolResult":
        return cls(
            ok=False,
            data=data,
            error_code=error_code,
            retryable=retryable,
            sources=sources or [],
            latency_ms=latency_ms,
            degraded=degraded,
        )


class ExecutionError(BaseModel):
    """Checkpoint-safe summary of a handled runtime failure."""

    component: str
    code: str
    category: ErrorCategory
    retryable: bool = False
    occurred_at: datetime = Field(default_factory=_utc_now)


class ExecutionTrace(BaseModel):
    """Operational event summary; never stores prompts or chain-of-thought."""

    event: str
    component: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=_utc_now)


class WorkflowRuntime(BaseModel):
    """Execution control state persisted alongside the business state."""

    run_id: str
    workflow_version: str
    current_node: str | None = None
    retry_counts: dict[str, int] = Field(default_factory=dict)
    degraded_components: list[str] = Field(default_factory=list)
    errors: list[ExecutionError] = Field(default_factory=list)
    traces: list[ExecutionTrace] = Field(default_factory=list)

    @classmethod
    def new(cls, *, run_id: str, workflow_version: str) -> "WorkflowRuntime":
        return cls(run_id=run_id, workflow_version=workflow_version)
