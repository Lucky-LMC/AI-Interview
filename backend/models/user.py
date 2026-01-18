# AI智能面试辅助系统V1.0，作者刘梦畅
"""
用户模型
"""
from sqlalchemy import Column, String

from backend.config import Base


class User(Base):
    """
    用户表

    字段：
        username: 主键，用户名
        password: 密码
    """

    __tablename__ = "users"

    user_name = Column(String(64), primary_key=True, nullable=False, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码")

