# AI模拟面试系统v1.0，作者刘梦畅
"""
LLM 辅助工具
提供统一的 LLM 实例
"""
from langchain_openai import ChatOpenAI
from backend.config import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, OPENAI_API_BASE

def get_llm() -> ChatOpenAI:
    """获取 LLM 实例"""
    return ChatOpenAI(
        model=MODEL_NAME,
        base_url=OPENAI_API_BASE,
        temperature=TEMPERATURE,
        api_key=OPENAI_API_KEY
    )


# 创建全局 LLM 实例
_llm_instance = None


def get_shared_llm() -> ChatOpenAI:
    """获取共享的 LLM 实例（单例模式）"""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = get_llm()
    return _llm_instance
