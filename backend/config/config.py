# AI智能面试辅助系统V1.0，作者刘梦畅
"""
系统配置模块
从 .env 文件加载配置参数
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（从项目根目录）
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


def get_required_env(key: str) -> str:
    """获取必需的环境变量，如果不存在则抛出异常"""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"环境变量 {key} 未设置，请在 .env 文件中配置")
    return value


# ========== LLM 配置 ==========
# OpenAI API 密钥
OPENAI_API_KEY = get_required_env("OPENAI_API_KEY")

# OpenAI API 基础 URL
OPENAI_API_BASE = get_required_env("OPENAI_API_BASE")

# 使用的模型名称
MODEL_NAME = get_required_env("MODEL_NAME")

# 温度参数：控制输出的随机性（0.0-1.0）
TEMPERATURE = float(get_required_env("TEMPERATURE"))

# Embedding 模型名称
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-zh-v1.5")

# ========== LangSmith 配置 ==========
# LangSmith API 密钥（用于追踪和调试）
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")

# ========== Tavily 配置 ==========
# Tavily API 密钥
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ========== 数据库配置 ==========
DB_HOST = get_required_env("DB_HOST")
DB_PORT = int(get_required_env("DB_PORT"))
DB_USER = get_required_env("DB_USER")
DB_PASSWORD = get_required_env("DB_PASSWORD")
DB_NAME = get_required_env("DB_NAME")

# 数据库连接 URL
DATABASE_URL = get_required_env("DATABASE_URL")
