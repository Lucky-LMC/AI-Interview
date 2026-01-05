# AI模拟面试系统v1.0，作者刘梦畅
"""
工作流图层 - LangGraph 工作流编排
用于定义面试系统的整体流程和节点间的流转逻辑
"""
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from backend.models.state import InterviewState
from backend.nodes import (
    parse_resume_node,    # 解析简历节点
    ask_question_node,    # 出题节点
    answer_node,          # 回答节点（中断点）
    evaluate_node,        # 评分节点
    check_finish_node,    # 检查是否结束节点
    generate_report_node  # 生成报告节点
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
    # 使用 agent 名称，便于在可视化中展示使用了 agent
    workflow.add_node("document_agent", parse_resume_node)      # 文档解析 Agent
    workflow.add_node("interviewer_agent", ask_question_node)   # 面试官 Agent
    workflow.add_node("answer", answer_node)                    # 用户回答节点
    workflow.add_node("evaluator_agent", evaluate_node)        # 评价 Agent（生成反馈）
    workflow.add_node("check_finish", check_finish_node)       # 检查是否完成所有轮次
    workflow.add_node("report_agent", generate_report_node)     # 报告生成 Agent
        

    # ========== 添加固定边（确定性流转）==========
    # START -> 文档解析 Agent，作为整个流程的起点
    workflow.add_edge(START, "document_agent")

    # 文档解析 Agent -> 面试官 Agent
    workflow.add_edge("document_agent", "interviewer_agent")

    # 面试官 Agent -> 回答：出题后等待用户回答
    workflow.add_edge("interviewer_agent", "answer")
    
    # 回答 -> 评价：用户回答后由评价 Agent 生成反馈
    workflow.add_edge("answer", "evaluator_agent")
    
    # 评价 -> 检查：生成反馈后检查是否完成所有轮次
    workflow.add_edge("evaluator_agent", "check_finish")
    
    # ========== 添加条件边（根据状态动态决策）==========
    # 从 check_finish 节点根据 is_finished 状态决定下一步
    workflow.add_conditional_edges(
        "check_finish",  # 源节点
        # 条件函数：根据 state 返回路径名称
        # lambda 参数: 返回值
        lambda state: "finish" if state['is_finished'] else "continue",
        {
            "continue": "interviewer_agent",  # 未完成 -> 继续下一轮出题（面试官 Agent）
            "finish": "report_agent"           # 已完成 -> 生成最终报告（报告生成 Agent）
        }
    )

    # 报告生成Agent -> END，作为整个流程的终点
    workflow.add_edge("report_agent", END)
    
    # ========== 编译并返回 ==========
    # 使用全局 checkpointer，确保所有请求共享同一个状态存储
    # 这样在 submit_answer 时能够正确恢复 start_interview 时保存的状态
    
    # 将定义好的工作流编译成可执行的图对象，并设置中断点
    return workflow.compile(
        checkpointer=_global_checkpointer,
        interrupt_before=["answer"]  # 中断点：在用户回答前中断，等待用户提交答案
    )