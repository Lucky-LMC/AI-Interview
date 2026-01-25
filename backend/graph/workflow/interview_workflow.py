# AI智能面试辅助系统V1.0，作者刘梦畅
"""
工作流图层 - LangGraph 工作流编排
用于定义面试系统的整体流程和节点间的流转逻辑
"""
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from backend.graph.state import InterviewState
from backend.graph.nodes import (
    parse_resume_node,       # 解析简历节点
    ask_question_node,       # 出题节点
    answer_node,             # 回答节点（中断点）

    check_finish_node,       # 检查是否结束节点
    check_finish_node,       # 检查是否完成所有轮次
    coach_node,              # 搜索学习资源节点（Coach Agent）
    generate_report_node     # 生成报告节点
)

# 全局 checkpointer 实例，确保所有请求共享同一个状态存储
_global_checkpointer = MemorySaver()


def create_interview_graph():
    """
    创建面试工作流图
    """
    # 创建状态图：基于 InterviewState 数据模型
    workflow = StateGraph(InterviewState)
    
    # ========== 添加节点 ==========
    # 每个节点对应一个业务功能，接收 state 并返回更新后的 state
    workflow.add_node("parse_resume", parse_resume_node)             # 简历解析节点
    workflow.add_node("interviewer_agent", ask_question_node)        # 面试官 Agent
    workflow.add_node("answer", answer_node)                         # 用户回答节点
    workflow.add_node("check_finish", check_finish_node)             # 检查是否完成所有轮次
    workflow.add_node("coach_agent", coach_node)                     # 搜索学习资源节点（Coach Agent）
    workflow.add_node("generate_report", generate_report_node)       # 生成最终报告节点
        

    # ========== 添加固定边（确定性流转）==========
    # START -> 简历解析节点，作为整个流程的起点
    workflow.add_edge(START, "parse_resume")

    # 简历解析节点 -> 面试官 Agent
    workflow.add_edge("parse_resume", "interviewer_agent")

    # 面试官 Agent -> 回答：出题后等待用户回答
    workflow.add_edge("interviewer_agent", "answer")
    
    # 回答 -> 检查：用户回答后直接检查是否完成所有轮次（移除即时评价）
    workflow.add_edge("answer", "check_finish")
    
    # ========== 添加条件边（根据状态动态决策）==========
    # 从 check_finish 节点根据 is_finished 状态决定下一步
    workflow.add_conditional_edges(
        "check_finish",  # 源节点
        # 条件函数：根据 state 返回路径名称
        lambda state: "finish" if state['is_finished'] else "continue",
        {
            "continue": "interviewer_agent",    # 未完成 -> 继续下一轮出题（面试官 Agent）
            "finish": "coach_agent"              # 已完成 -> 搜索学习资源（Coach Agent）
        }
    )

    # 搜索资源 -> 生成报告
    workflow.add_edge("coach_agent", "generate_report")
    
    # 生成报告 -> END，作为整个流程的终点
    workflow.add_edge("generate_report", END)
    
    # ========== 编译并返回 ==========
    # 使用全局 checkpointer，确保所有请求共享同一个状态存储
    # 这样在 submit_answer 时能够正确恢复 start_interview 时保存的状态
    
    # 将定义好的工作流编译成可执行的图对象，并设置中断点
    return workflow.compile(
        checkpointer=_global_checkpointer,
        interrupt_before=["answer"]  # 中断点：在用户回答前中断，等待用户提交答案
    )
