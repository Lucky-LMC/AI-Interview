# AI智能面试辅助系统V1.0，作者刘梦畅
"""
面试反馈工具定义
包含学习资源搜索工具
"""
from langchain_core.tools import tool


@tool
def search_learning_resources(topic: str) -> str:
    """
    联网搜索学习资源，包括书籍、课程、教程等。
    
    Args:
        topic: 需要学习的主题，如"Redis缓存"、"分布式事务"、"系统设计"
    
    Returns:
        搜索到的学习资源，包含书籍、课程、文章链接等
    """
    from backend.config import TAVILY_API_KEY
    from tavily import TavilyClient

    if not TAVILY_API_KEY:
        print("[search_learning_resources] 未配置 TAVILY_API_KEY")
        return "搜索失败: 未配置 TAVILY_API_KEY"

    try:
        print(f"[search_learning_resources] 正在搜索: {topic}")
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
        
        # 直接使用此 Topic 进行搜索
        query = topic
        
        # 执行搜索
        response = tavily.search(query=query, search_depth="advanced", max_results=2)
        results = response.get("results", [])
        
        if results:
            # 整理搜索结果
            resources = []
            for res in results:
                resources.append(f"- [{res['title']}]({res['url']})\n  {res['content'][:150]}...")
            
            result_text = "\n\n".join(resources)
            print(f"[search_learning_resources] 找到 {len(results)} 个资源")
            return f"【{topic} - 学习资源】\n{result_text}"
        else:
            return f"未找到关于 {topic} 的学习资源"
            
    except Exception as e:
        print(f"[search_learning_resources] 搜索失败: {e}")
        return f"搜索失败: {str(e)}"


# 导出工具列表
feedback_tools = [search_learning_resources]
