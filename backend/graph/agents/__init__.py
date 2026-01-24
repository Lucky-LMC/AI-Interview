# AI智能面试辅助系统V1.0，作者刘梦畅
"""
Agent 模块
"""
from backend.graph.agents.interviewer_agent import (
    create_interviewer_agent,
    interviewer_agent,
    INTERVIEWER_AGENT_PROMPT
)
from backend.graph.agents.coach_agent import (
    create_coach_agent,
    coach_agent,
    COACH_AGENT_PROMPT
)

__all__ = [
    "create_interviewer_agent",
    "interviewer_agent",
    "INTERVIEWER_AGENT_PROMPT",
    "create_coach_agent",
    "coach_agent",
    "COACH_AGENT_PROMPT"
]

