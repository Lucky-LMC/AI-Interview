# AI模拟面试系统v1.0，作者刘梦畅
"""
回答节点
接收用户答案（中断点）
"""
from backend.graph.state import InterviewState


def answer_node(state: InterviewState) -> InterviewState:
    """
    回答节点：接收用户答案
    注意：保留是为了中断机制的兼容性
    """
    # 答案已经在 state 中了，直接返回
    return state
