"""Official LangChain middleware composition for bounded Agent execution."""

from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ModelRetryMiddleware,
    ToolCallLimitMiddleware,
    ToolRetryMiddleware,
)

from .errors import ErrorCategory, classify_exception
from .policies import AgentPolicy
from .contracts import ToolResult


def _is_transient(exc: Exception) -> bool:
    return classify_exception(exc) is ErrorCategory.TRANSIENT


def _safe_tool_failure(_exc: Exception) -> str:
    return ToolResult.failure(
        error_code="TOOL_TEMPORARILY_UNAVAILABLE",
        retryable=True,
    ).model_dump_json()


def build_agent_middleware(policy: AgentPolicy) -> list:
    """Build middleware in retry-before-budget order for one Agent role."""

    middleware = [
        ModelRetryMiddleware(
            max_retries=policy.model_retries,
            retry_on=_is_transient,
            on_failure="continue",
        ),
        ToolRetryMiddleware(
            max_retries=policy.tool_retries,
            retry_on=_is_transient,
            on_failure=_safe_tool_failure,
            initial_delay=0.2,
            max_delay=1.0,
            jitter=False,
        ),
        ModelCallLimitMiddleware(
            run_limit=policy.model_run_limit,
            exit_behavior="end",
        ),
        ToolCallLimitMiddleware(
            run_limit=policy.global_tool_run_limit,
            exit_behavior="continue",
        ),
    ]
    middleware.extend(
        ToolCallLimitMiddleware(
            tool_name=tool_name,
            run_limit=run_limit,
            exit_behavior="continue",
        )
        for tool_name, run_limit in policy.tool_limits.items()
    )
    return middleware
