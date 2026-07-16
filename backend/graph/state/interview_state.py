# AI智能面试辅助系统V1.0，作者刘梦畅
"""
面试状态数据模型
定义面试过程中需要维护的所有状态信息
使用 TypedDict 确保类型安全，便于 IDE 提示和类型检查
"""
from typing import Any, TypedDict, List, Dict

from backend.graph.runtime.contracts import WorkflowRuntime


class InterviewState(TypedDict):
    """
    面试状态数据结构
    
    这个状态会在整个面试流程中传递和更新
    每个节点接收当前状态，处理后返回更新后的状态
    """
    
    # ========== 轮次控制 ==========
    round: int          # 当前面试轮次（从 0 开始）
    max_rounds: int     # 最大面试轮数
    
    # ========== 简历信息 ==========
    resume_path: str    # 简历 PDF 文件路径
    resume_text: str    # LLM 提取的简历关键信息（结构化摘要）
    target_position: str  # LLM 提取的目标岗位
    resume_validation: Dict[str, Any]  # 简历结构化质量校验结果
    resume_valid: bool  # 简历结构化信息是否通过质量门禁
    
    # ========== 面试记录 ==========
    # 存储所有轮次的问答记录
    # 每条记录包含：问题、回答
    history: List[Dict[str, str]]  # [{"question": "", "answer": ""}]
    question_review: Dict[str, Any]  # 最新问题质量审查结果
    question_retry_count: int  # 当前问题质量审查触发的重写次数
    question_rewrite_instruction: str  # 问题重写要求
    
    # ========== 学习资源 ==========
    learning_resources: str  # Coach Agent 搜索到的学习资源
    
    # ========== 评分 ==========
    # 最终面试报告
    report: str

    # ========== 面试控制 ==========
    is_finished: bool   # 标识面试是否已完成所有轮次

    # ========== 运行控制（与业务状态分离） ==========
    runtime: WorkflowRuntime
