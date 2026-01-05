# AI模拟面试系统v1.0，作者刘梦畅
"""
数据库引擎与会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import DATABASE_URL


engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    future=True
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

Base = declarative_base()


def init_db() -> None:
    """
    初始化数据库（在应用启动时调用）
    """
    # 避免循环导入，在函数内部导入模型
    from backend.models import User, InterviewRecord  # noqa: WPS433,F401

    Base.metadata.create_all(bind=engine)

