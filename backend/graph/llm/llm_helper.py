# AI智能面试辅助系统V1.0，作者刘梦畅
"""
LLM 辅助工具
提供统一的 LLM 实例
"""
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.config import (
    OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, OPENAI_API_BASE,
    GEMINI_API_KEY, GEMINI_MODEL_NAME, GEMINI_API_BASE
)

# ========== OpenAI LLM ==========
def get_openai_llm() -> ChatOpenAI:
    """获取 OpenAI LLM 实例"""
    return ChatOpenAI(
        model=MODEL_NAME,
        base_url=OPENAI_API_BASE,
        temperature=TEMPERATURE,
        api_key=OPENAI_API_KEY
    )


# 创建全局单例实例
openai_llm = get_openai_llm()


# ========== Gemini LLM ==========
def get_gemini_llm() -> ChatGoogleGenerativeAI:
    """获取 Gemini LLM 实例"""
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL_NAME,
        google_api_key=GEMINI_API_KEY,
        temperature=TEMPERATURE,
        client_options={"api_endpoint": GEMINI_API_BASE}
    )


# 创建全局单例实例
gemini_llm = get_gemini_llm()
