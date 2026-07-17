"""Stable error taxonomy used by tools, agents, and workflow nodes."""

from enum import Enum


class ErrorCategory(str, Enum):
    """Controls whether an operation should retry, fail fast, or degrade."""

    TRANSIENT = "transient"
    VALIDATION = "validation"
    PERMANENT = "permanent"


class WorkflowExecutionError(Exception):
    """Base error with a safe message that may be shown outside the backend."""

    category = ErrorCategory.PERMANENT
    retryable = False
    public_message = "操作暂时无法完成"

    def __init__(self, detail: str = "") -> None:
        super().__init__(detail)
        self.detail = detail


class TransientExecutionError(WorkflowExecutionError):
    category = ErrorCategory.TRANSIENT
    retryable = True
    public_message = "服务暂时不可用，请稍后重试"


class ValidationExecutionError(WorkflowExecutionError):
    category = ErrorCategory.VALIDATION
    public_message = "输入内容未通过校验"


class PermanentExecutionError(WorkflowExecutionError):
    category = ErrorCategory.PERMANENT


class MissingConfigurationError(PermanentExecutionError):
    """Raised when a required integration has not been configured."""

    public_message = "外部能力尚未配置"

    def __init__(self, setting_name: str) -> None:
        super().__init__(setting_name)
        self.setting_name = setting_name


_TRANSIENT_BUILTINS = (TimeoutError, ConnectionError)
_VALIDATION_BUILTINS = (ValueError, TypeError)


def classify_exception(exc: Exception) -> ErrorCategory:
    """Classify errors without leaking their raw messages to callers."""

    if isinstance(exc, WorkflowExecutionError):
        return exc.category
    if isinstance(exc, _TRANSIENT_BUILTINS):
        return ErrorCategory.TRANSIENT
    if isinstance(exc, _VALIDATION_BUILTINS):
        return ErrorCategory.VALIDATION
    error_name = type(exc).__name__.lower()
    if any(marker in error_name for marker in ("timeout", "connection", "ratelimit")):
        return ErrorCategory.TRANSIENT
    status_code = getattr(exc, "status_code", None)
    if status_code == 429 or isinstance(status_code, int) and status_code >= 500:
        return ErrorCategory.TRANSIENT
    return ErrorCategory.PERMANENT
