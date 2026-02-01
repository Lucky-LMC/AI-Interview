# AI智能面试辅助系统V1.0，作者刘梦畅
"""
顾问对话记录模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from backend.config import Base


class ConsultantRecord(Base):
    """
    顾问对话记录表
    
    字段：
        thread_id: 主键，会话ID（与面试记录保持一致的命名）
        user_name: 外键，用户名（关联 users 表）
        title: 会话标题（从第一条用户消息提取）
        messages: 对话历史（JSON格式）
        created_at: 创建时间
        updated_at: 更新时间
    """
    
    __tablename__ = "consultant_records"
    
    # 主键
    thread_id = Column(String(64), primary_key=True, nullable=False, comment="会话ID")
    
    # 外键：关联用户表
    user_name = Column(String(64), ForeignKey("users.user_name", ondelete="CASCADE"), nullable=False, comment="用户名（外键）")
    
    # 会话标题
    title = Column(String(100), nullable=False, default="新咨询会话", comment="会话标题")
    
    # 对话历史（JSON格式）
    # 格式: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    messages = Column(JSON, nullable=False, default=list, comment="对话历史（JSON格式）")
    
    # 创建时间
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    
    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False, comment="更新时间")
    
    # 关系：关联用户（用于反向查询）
    user = relationship("User", backref="consultant_records")
