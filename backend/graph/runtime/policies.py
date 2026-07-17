"""Explicit, reviewable execution budgets for each prebuilt Agent."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentPolicy:
    model_retries: int
    tool_retries: int
    model_run_limit: int
    global_tool_run_limit: int
    tool_limits: dict[str, int]

    @classmethod
    def interviewer(cls) -> "AgentPolicy":
        return cls(
            model_retries=1,
            tool_retries=1,
            model_run_limit=4,
            global_tool_run_limit=1,
            tool_limits={"search_interview_questions": 1},
        )

    @classmethod
    def feedback(cls) -> "AgentPolicy":
        return cls(
            model_retries=1,
            tool_retries=1,
            model_run_limit=6,
            global_tool_run_limit=3,
            tool_limits={"search_learning_resources": 3},
        )

    @classmethod
    def consultant(cls) -> "AgentPolicy":
        return cls(
            model_retries=1,
            tool_retries=1,
            model_run_limit=5,
            global_tool_run_limit=2,
            tool_limits={"search_knowledge_base": 1, "tavily_search": 1},
        )
