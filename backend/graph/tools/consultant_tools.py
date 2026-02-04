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
    
    该工具使用语义检索技术，能够理解用户问题的含义，找到最相关的知识点。
    知识库包含：简历优化、自我介绍、行为面试、薪资谈判、STAR法则、技术面试等内容。
    
    Args:
        query: 用户的问题或查询关键词，例如"如何写简历"、"怎么谈薪资"、"STAR法则是什么"
        
    Returns:
        str: 检索到的相关内容，如果没有找到则返回 "无相关信息"
    """
    print(f"[Consultant Agent - search_knowledge_base] 开始向量检索，查询: {query}")
    
    try:
        # 获取向量数据库
        vectorstore = get_vectorstore()
        
        # 语义检索（返回最相关的 2 个文档块）
        results = vectorstore.similarity_search_with_score(query, k=2)
        
        if not results:
            print(f"[Consultant Agent - search_knowledge_base] ❌ 未找到相关内容")
            return "知识库中没有找到相关内容。请立即使用 tavily_search 工具进行联网搜索以获取最新信息。"
        
        # 过滤相似度过低的结果（score 越小越相似，< 0.8 表示相关）
        relevant_results = [(doc, score) for doc, score in results if score < 0.8]
        
        if not relevant_results:
            print(f"[Consultant Agent - search_knowledge_base] ❌ 相似度不足（最佳相似度: {results[0][1]:.3f}，需要 < 0.8），触发联网搜索")
            return "知识库中没有找到相关内容。请立即使用 tavily_search 工具进行联网搜索以获取最新信息。"
        
        # 合并检索结果
        matched_content = []
        for doc, score in relevant_results:
            print(f"[Consultant Agent - search_knowledge_base] ✓ 找到相关内容 (相似度: {score:.3f})")
            matched_content.append(doc.page_content)
        
        result = "\n\n".join(matched_content)
        print(f"[Consultant Agent - search_knowledge_base] ✅ 返回 {len(relevant_results)} 个相关文档块")
        
        return result
        
    except Exception as e:
        print(f"[Consultant Agent - search_knowledge_base] ❌ 检索失败: {e}")
        import traceback
        traceback.print_exc()
        return "知识库检索失败。请立即使用 tavily_search 工具进行联网搜索以获取最新信息。"


@tool("tavily_search")
def tavily_search(query: str) -> str:
    """
    使用 Tavily 联网搜索最新的面试相关信息（兜底机制）。
    
    当私有知识库中没有相关信息时，使用此工具搜索互联网上的最新内容。
    适用于：最新的行业动态、公司面试真题、新兴技术面试题等。
    
    Args:
        query: 搜索查询，例如"2024年字节跳动面试题"、"最新的前端面试趋势"
        
    Returns:
        str: 搜索结果，包含标题、链接和摘要
    """
    from tavily import TavilyClient
    import time

    print(f"[Consultant Agent - tavily_search] 开始联网搜索，查询: {query}")

    if not TAVILY_API_KEY:
        print("[Consultant Agent - tavily_search] ❌ 未配置 TAVILY_API_KEY")
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
                for res in results:
                    search_results.append(f"- [{res['title']}]({res['url']})\n  {res['content'][:200]}...")
                
                result_text = "\n\n".join(search_results)
                print(f"[Consultant Agent - tavily_search] ✅ 找到 {len(results)} 个搜索结果")
                return f"【联网搜索结果】\n{result_text}"
            else:
                print(f"[Consultant Agent - tavily_search] ⚠️ 未找到相关信息")
                return f"未找到关于 {query} 的相关信息"
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"[Consultant Agent - tavily_search] ⚠️ 搜索失败（第 {attempt + 1} 次），重试中...")
                time.sleep(1)  # 等待1秒后重试
                continue
            else:
                print(f"[Consultant Agent - tavily_search] ❌ 搜索失败（已重试 {max_retries} 次）: {e}")
                return f"联网搜索暂时不可用，请稍后再试"


# 导出工具列表（顺序很重要！优先使用知识库）
consultant_tools = [search_knowledge_base, tavily_search]
