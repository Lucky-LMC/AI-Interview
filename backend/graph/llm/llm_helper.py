# AI智能面试辅助系统V1.0，作者：刘梦畅
"""
LLM 辅助工具
提供统一的 LLM 实例和 Embedding 模型
"""
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from backend.config import (
    OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, OPENAI_API_BASE, EMBEDDING_MODEL
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


# ========== Embedding 模型 ==========
def get_openai_embeddings() -> OpenAIEmbeddings:
    """获取 OpenAI Embedding 模型实例（使用硅基流动平台）"""
    return OpenAIEmbeddings(
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        model=EMBEDDING_MODEL  # 从配置文件读取
    )


# 创建全局单例实例
openai_embeddings = get_openai_embeddings()
