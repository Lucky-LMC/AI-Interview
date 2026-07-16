"""Safe execution wrapper shared by all LangChain tools."""

from collections.abc import Callable
from time import perf_counter
from typing import Any

from .contracts import ToolResult
from .errors import ErrorCategory, MissingConfigurationError, classify_exception


def _elapsed_ms(started: float) -> int:
    return max(0, round((perf_counter() - started) * 1000))


def error_code_for(name: str, exc: Exception) -> str:
    prefix = name.upper().replace("-", "_").replace(" ", "_")
    if isinstance(exc, MissingConfigurationError):
        return f"{prefix}_NOT_CONFIGURED"
    if isinstance(exc, TimeoutError):
        return f"{prefix}_TIMEOUT"
    category = classify_exception(exc)
    if category is ErrorCategory.VALIDATION:
        return f"{prefix}_INVALID_INPUT"
    if category is ErrorCategory.TRANSIENT:
        return f"{prefix}_TEMPORARILY_UNAVAILABLE"
    return f"{prefix}_FAILED"


def timed_tool_call(
    name: str,
    call: Callable[[], Any],
    *,
    missing_config: str | None = None,
) -> ToolResult:
    """Execute a tool operation and normalize failures without leaking details."""

    started = perf_counter()
    try:
        if missing_config:
            raise MissingConfigurationError(missing_config)
        data = call()
        if isinstance(data, ToolResult):
            data.latency_ms = _elapsed_ms(started)
            return data
        return ToolResult.success(data=data, latency_ms=_elapsed_ms(started))
    except Exception as exc:
        category = classify_exception(exc)
        return ToolResult.failure(
            error_code=error_code_for(name, exc),
            retryable=category is ErrorCategory.TRANSIENT,
            latency_ms=_elapsed_ms(started),
        )
