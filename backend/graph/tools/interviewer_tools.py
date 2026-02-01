# AI智能面试辅助系统V1.0，作者刘梦畅
"""
面试官工具定义
包含联网搜索和简历出题两个工具
"""
from langchain_core.tools import tool
from backend.graph.llm import openai_llm  # 工具内部的文本处理用 DeepSeek


@tool
def search_interview_questions(topic: str) -> str:
    """
    联网搜索相关的面试题目。
    
    Args:
        topic: 搜索话题，可以是岗位名称（如"Java后端"），也可以是具体技术点（如"Redis分布式锁"、"Spring循环依赖"）
    
    Returns:
        搜索到的面试题目列表
    """
    from backend.config import TAVILY_API_KEY
    from tavily import TavilyClient

    print(f"[search_interview_questions] 收到搜索请求: {topic}")

    # 尝试使用 Tavily 进行真实搜索
    if TAVILY_API_KEY:
        try:
            tavily = TavilyClient(api_key=TAVILY_API_KEY)
            
            # 直接使用 Agent 提供的 topic 进行搜索，保持最大灵活性
            search_query = topic
            print(f"[search_interview_questions] 执行搜索 Query: {search_query}")
            
            # 执行搜索，获取包含内容的上下文
            response = tavily.search(query=search_query, search_depth="advanced", max_results=3)
            results = response.get("results", [])
            
            if results:
                # 提取搜索结果内容
                context_parts = []
                for i, res in enumerate(results):
                    context_parts.append(f"来源 {i+1}: {res['title']}\n{res['content']}")
                
                search_context = "\n\n".join(context_parts)
                
                # 使用 LLM 从搜索结果中提取并整理问题
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
                questions = result.content.strip()
                print(f"[search_interview_questions] 搜索并整理的问题:\n{questions}")
                return f"【{topic} - 搜索结果】\n{questions}"
                
        except Exception as e:
            print(f"[search_interview_questions] Tavily 搜索失败: {e}")
            return f"搜索失败: {str(e)}"
    
    # 如果没有配置 Tavily API Key
    print("[search_interview_questions] 未配置 TAVILY_API_KEY")
    return "搜索失败: 未配置 TAVILY_API_KEY"



# 导出工具列表
interviewer_tools = [search_interview_questions]
