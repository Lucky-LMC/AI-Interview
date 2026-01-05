# AI模拟面试系统v1.0，作者刘梦畅
"""
配置模块
"""
from .config import (
    OPENAI_API_KEY,
    OPENAI_API_BASE,
    MODEL_NAME,
    TEMPERATURE,
    MAX_ROUNDS,
    DATABASE_URL,
    DB_HOST,
    DB_PORT,
    DB_USER,
    DB_PASSWORD,
    DB_NAME
)

__all__ = [
    "OPENAI_API_KEY",
    "OPENAI_API_BASE",
    "MODEL_NAME",
    "TEMPERATURE",
    "MAX_ROUNDS",
    "DATABASE_URL",
    "DB_HOST",
    "DB_PORT",
    "DB_USER",
    "DB_PASSWORD",
    "DB_NAME"
]
