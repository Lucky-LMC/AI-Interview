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
    print(f"[Consultant] 📖 知识库检索内容: {query}")
    
    try:
        # 获取向量数据库
        vectorstore = get_vectorstore()
        
        # 语义检索（返回最相关的 2 个文档块）
        results = vectorstore.similarity_search_with_score(query, k=2)
        
        if not results:
            print(f"[Consultant] ❌ 知识库未命中 (无结果)")
            return "知识库中没有找到相关内容。请立即使用 tavily_search 工具进行联网搜索以获取最新信息。"
        
        # 过滤相似度过低的结果（score 越小越相似）
        # 调整阈值：0.8 -> 0.6（更严格，避免匹配到不相关的通用内容）
        threshold = 0.6
        relevant_results = [(doc, score) for doc, score in results if score < threshold]
        
        if not relevant_results:
            print(f"[Consultant] ❌ 知识库未命中 (最佳相似度: {results[0][1]:.3f} > {threshold})")
            return "知识库中没有找到相关内容。请立即使用 tavily_search 工具进行联网搜索以获取最新信息。"
        
        # 合并检索结果
        matched_content = []
        for doc, score in relevant_results:
            preview = doc.page_content[:100].replace('\n', ' ') + "..."
            print(f"[Consultant] ✅ 命中知识片段 (Score: {score:.3f}): {preview}")
            matched_content.append(doc.page_content)
        
        result = "\n\n".join(matched_content)
        return result
        
    except Exception as e:
        print(f"[Consultant] ❌ 知识库检索错误: {e}")
        import traceback
        traceback.print_exc()
        return "知识库检索失败。请立即使用 tavily_search 工具进行联网搜索以获取最新信息。"


@tool("tavily_search")
def tavily_search(query: str) -> str:
    """
    使用 Tavily 联网搜索最新的面试相关信息（兜底机制）。
    ...
    """
    from tavily import TavilyClient
    import time

    print(f"[Consultant] 🌐 联网搜索内容: {query}")

    if not TAVILY_API_KEY:
        print("[Consultant] ❌ 未配置 TAVILY_API_KEY")
        return "搜索失败: 未配置 TAVILY_API_KEY"

    # 重试机制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            tavily = TavilyClient(api_key=TAVILY_API_KEY)
            
            # 执行搜索
            response = tavily.search(query=query, search_depth="basic", max_results=3)
            results = response.get("results", [])
            
            if results:
                # 整理搜索结果
                search_results = []
                print(f"[Consultant] ✅ 联网搜索成功，找到 {len(results)} 条结果:")
                for res in results:
                    print(f"  - [{res['title']}] {res['url']}")
                    search_results.append(f"- [{res['title']}]({res['url']})\n  {res['content'][:200]}...")
                
                result_text = "\n\n".join(search_results)
                return f"【联网搜索结果】\n{result_text}"
            else:
                print(f"[Consultant] ⚠️ 联网搜索未找到结果")
                return f"未找到关于 {query} 的相关信息"
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[Consultant] ⚠️ 搜索失败（第 {attempt + 1} 次），重试中...")
                time.sleep(1)  # 等待1秒后重试
                continue
            else:
                print(f"[Consultant] ❌ 搜索失败（已重试 {max_retries} 次）: {e}")
                return f"联网搜索暂时不可用，请稍后再试"


# 导出工具列表（顺序很重要！优先使用知识库）
consultant_tools = [search_knowledge_base, tavily_search]
