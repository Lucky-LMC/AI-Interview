# AI模拟面试系统v1.0，作者刘梦畅
"""
系统配置模块
从 .env 文件加载配置参数
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# ========== LLM 配置 ==========
# OpenAI API 密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# OpenAI API 基础 URL
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

# 使用的模型名称
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")

# 温度参数：控制输出的随机性（0.0-1.0）
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# ========== 面试配置 ==========
# 默认面试轮数
MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", "3"))

# ========== 数据库配置 ==========
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "Interview")

# 允许直接通过 DATABASE_URL 覆盖整个连接串
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)
