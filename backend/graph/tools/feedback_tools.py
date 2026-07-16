# AI智能面试辅助系统V1.0，作者刘梦畅
"""
面试反馈工具定义
包含学习资源搜索工具
"""
from langchain_core.tools import tool
from backend.graph.runtime import SourceRef, ToolResult
from backend.graph.runtime.tool_runtime import timed_tool_call


@tool
def search_learning_resources(topic: str) -> str:
    """
    联网搜索学习资源，包括书籍、课程、教程等。
    
    Args:
        topic: 需要学习的主题，如"Redis缓存"、"分布式事务"、"系统设计"
    
    Returns:
        搜索到的学习资源，包含书籍、课程、文章链接等
    """
    from backend import config
    from tavily import TavilyClient

    def _search() -> ToolResult:
        tavily = TavilyClient(api_key=config.TAVILY_API_KEY)
        response = tavily.search(
            query=topic,
            search_depth="advanced",
            max_results=2,
        )
        results = response.get("results", [])
        sources = [
            SourceRef(title=item.get("title", "学习资源"), url=item.get("url"))
            for item in results
        ]
        resources = [
            {
                "title": item.get("title", "学习资源"),
                "url": item.get("url"),
                "summary": item.get("content", "")[:300],
            }
            for item in results
        ]
        return ToolResult.success(
            data={"topic": topic, "resources": resources},
            sources=sources,
            degraded=not bool(resources),
        )

    result = timed_tool_call(
        "learning_resource_search",
        _search,
        missing_config=None if config.TAVILY_API_KEY else "TAVILY_API_KEY",
    )
    return result.model_dump_json()


# 导出工具列表
feedback_tools = [search_learning_resources]
