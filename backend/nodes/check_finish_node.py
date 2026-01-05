# AI模拟面试系统v1.0，作者刘梦畅
"""
检查完成节点
检查是否结束面试
"""
from backend.models.state import InterviewState


def check_finish_node(state: InterviewState) -> InterviewState:
    """
    检查是否结束面试
    """
    new_state = state.copy()
    new_state['is_finished'] = state['round'] >= state['max_rounds']
    return new_state

