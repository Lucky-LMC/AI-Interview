# AI智能面试辅助系统V1.0，作者刘梦畅
"""
面试记录模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from backend.config import Base


class InterviewRecord(Base):
    """
    面试记录表
    
    字段：
        thread_id: 主键，会话ID
        user_name: 外键，用户名（关联 users 表）
        resume_text: 简历文本内容
        history: 面试记录（JSON格式，包含每一轮的提问、回答、反馈）
        report: 最终面试报告
        created_at: 创建时间
    """
    
    __tablename__ = "interview_records"
    
    # 主键
    thread_id = Column(String(64), primary_key=True, nullable=False, comment="会话ID")
    
    # 外键：关联用户表
    user_name = Column(String(64), ForeignKey("users.user_name", ondelete="CASCADE"), nullable=False, comment="用户名（外键）")
    
    # 简历文本
    resume_text = Column(Text, nullable=False, comment="简历文本内容")
    
    # 面试记录（JSON格式）
    # 格式: [{"question": "", "answer": ""}, ...]
    history = Column(JSON, nullable=False, default=list, comment="面试记录（JSON格式）")
    
    # 最终面试报告
    report = Column(Text, nullable=True, comment="最终面试报告")
    
    # 创建时间（使用本地时间）
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    
    # 关系：关联用户（用于反向查询）
    user = relationship("User", backref="interview_records")

