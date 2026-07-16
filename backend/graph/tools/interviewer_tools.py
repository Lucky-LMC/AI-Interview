# AI智能面试辅助系统V1.0，作者刘梦畅
"""
面试官工具定义
包含联网搜索和简历出题两个工具
"""
from langchain_core.tools import tool
from backend.graph.llm import openai_llm  # 工具内部的文本处理用 DeepSeek
from backend.graph.runtime import SourceRef, ToolResult
from backend.graph.runtime.tool_runtime import timed_tool_call


@tool
def search_interview_questions(topic: str) -> str:
    """
    联网搜索相关的面试题目。
    
    Args:
        topic: 搜索话题，可以是岗位名称（如"Java后端"），也可以是具体技术点（如"Redis分布式锁"、"Spring循环依赖"）
    
    Returns:
        搜索到的面试题目列表
    """
    from backend import config
    from tavily import TavilyClient

    def _search() -> ToolResult:
        tavily = TavilyClient(api_key=config.TAVILY_API_KEY)
        response = tavily.search(
            query=topic,
            search_depth="advanced",
            max_results=3,
        )
        results = response.get("results", [])
        sources = [
            SourceRef(title=item.get("title", "搜索结果"), url=item.get("url"))
            for item in results
        ]
        if not results:
            return ToolResult.success(
                data={"topic": topic, "questions": []},
                sources=[],
                degraded=True,
            )

        search_context = "\n\n".join(
            f"来源 {index}: {item.get('title', '')}\n{item.get('content', '')}"
            for index, item in enumerate(results, start=1)
        )
        prompt = f"""请根据以下联网搜索到的内容，提炼出 3 个最高质量的面试问题：

搜索话题：{topic}

搜索结果：
{search_context}

请只输出 3 个具体的面试问题，直接输出问题内容，不要编号、不要前缀。
要求：
1. 问题必须基于搜索结果
2. 问题要真实、常见、有深度
3. 优先选择质量高的问题
"""
        result = openai_llm.invoke(prompt)
        questions = [
            line.strip(" -0123456789.、")
            for line in result.content.splitlines()
            if line.strip()
        ]
        return ToolResult.success(
            data={"topic": topic, "questions": questions[:3]},
            sources=sources,
        )

    result = timed_tool_call(
        "interview_search",
        _search,
        missing_config=None if config.TAVILY_API_KEY else "TAVILY_API_KEY",
    )
    return result.model_dump_json()



# 导出工具列表
interviewer_tools = [search_interview_questions]
