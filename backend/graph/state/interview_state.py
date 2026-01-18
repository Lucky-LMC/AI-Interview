# AI模拟面试系统v1.0，作者刘梦畅
"""
面试状态数据模型
定义面试过程中需要维护的所有状态信息
使用 TypedDict 确保类型安全，便于 IDE 提示和类型检查
"""
from typing import TypedDict, List, Dict


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
    resume_text: str    # 解析后的简历文本内容
    
    # ========== 面试记录 ==========
    # 存储所有轮次的问答记录
    # 每条记录包含：问题、回答、反馈（包含评价和改进建议）
    history: List[Dict[str, str]]  # [{"question": "", "answer": "", "feedback": ""}]
    
    # ========== 评分 ==========
    # 最终面试报告
    report: str

    # ========== 面试控制 ==========
    is_finished: bool   # 标识面试是否已完成所有轮次
