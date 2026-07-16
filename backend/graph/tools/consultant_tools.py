# AI智能面试辅助系统V1.0，作者刘梦畅
"""
面试顾问工具 - RAG 版本
使用 Chroma 向量数据库进行语义检索
"""
from langchain_core.tools import tool
from langchain_chroma import Chroma
from pathlib import Path
from backend.graph.llm import openai_embeddings
from backend.config import TAVILY_API_KEY
from backend.graph.runtime import SourceRef, ToolResult
from backend.graph.runtime.tool_runtime import timed_tool_call
from backend.graph.rag.service import RagService

# Chroma 数据库路径
CHROMA_DB_PATH = Path(__file__).parent.parent / "rag" / "chroma_db"

# 全局变量：向量数据库实例（懒加载）
_vectorstore = None


def get_vectorstore():
    """
    获取向量数据库实例（单例模式）
    """
    global _vectorstore
    
    if _vectorstore is None:
        # 检查数据库是否存在
        if not CHROMA_DB_PATH.exists():
            raise FileNotFoundError(
                f"向量数据库不存在: {CHROMA_DB_PATH}\n"
                f"请先运行初始化脚本: python backend/graph/rag/init_vectorstore.py"
            )
        
        # 加载向量数据库
        _vectorstore = Chroma(
            persist_directory=str(CHROMA_DB_PATH),
            embedding_function=openai_embeddings,
            collection_name="interview_knowledge"
        )
    
    return _vectorstore


@tool("search_knowledge_base")
def search_knowledge_base(query: str) -> str:
    """
    从私有向量知识库中检索面试相关信息（使用 RAG 技术）。
    ...
    """
    def _retrieve() -> ToolResult:
        vectorstore = get_vectorstore()
        rag_result = RagService(vectorstore).retrieve(query, k=4)
        sources = [document.source for document in rag_result.documents]
        return ToolResult.success(
            data=rag_result.model_dump(mode="json"),
            sources=sources,
            degraded=rag_result.fallback_required,
        )

    return timed_tool_call("knowledge_base", _retrieve).model_dump_json()


@tool("tavily_search")
def tavily_search(query: str) -> str:
    """
    使用 Tavily 联网搜索最新的面试相关信息（兜底机制）。
    ...
    """
    from tavily import TavilyClient

    def _search() -> ToolResult:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
        response = tavily.search(query=query, search_depth="basic", max_results=3)
        results = response.get("results", [])
        sources = [
            SourceRef(title=item.get("title", "联网搜索"), url=item.get("url"))
            for item in results
        ]
        items = [
            {
                "title": item.get("title", "联网搜索"),
                "url": item.get("url"),
                "summary": item.get("content", "")[:400],
            }
            for item in results
        ]
        return ToolResult.success(
            data={"query": query, "items": items},
            sources=sources,
            degraded=not bool(items),
        )

    return timed_tool_call(
        "tavily",
        _search,
        missing_config=None if TAVILY_API_KEY else "TAVILY_API_KEY",
    ).model_dump_json()


# 导出工具列表（顺序很重要！优先使用知识库）
consultant_tools = [search_knowledge_base, tavily_search]
