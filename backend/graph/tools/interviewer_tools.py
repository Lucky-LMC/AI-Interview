# AI智能面试辅助系统V1.0，作者刘梦畅
"""
面试官工具定义
包含联网搜索和简历出题两个工具
"""
from langchain_core.tools import tool
from backend.graph.llm import openai_llm


@tool
def search_interview_questions(position: str, question_type: str = "技术") -> str:
    """
    根据岗位联网搜索面试题目。
    
    Args:
        position: 目标岗位名称，如"Java后端开发工程师"、"前端开发工程师"
        question_type: 问题类型，可选值："技术"、"沟通"、"HR"
    
    Returns:
        搜索到的面试题目列表
    """
    # TODO: 后续可接入真实搜索API（如Tavily、SerpAPI等）
    # 目前使用 LLM 模拟搜索结果
    
    prompt = f"""你是一个面试题目搜索引擎。请根据以下信息，提供5个真实、常见的面试问题：

岗位：{position}
问题类型：{question_type}类问题

请输出5个具体的面试问题，每个问题一行，只输出问题内容，不要编号。
要求：
1. 问题要真实、常见、有深度
2. 针对该岗位的核心能力
3. {question_type}类问题要符合该轮次的考察目标
"""
    
    try:
        result = openai_llm.invoke(prompt)
        questions = result.content.strip()
        print(f"[search_interview_questions] 搜索到的问题:\n{questions}")
        return f"【{position} - {question_type}类面试题】\n{questions}"
    except Exception as e:
        print(f"[search_interview_questions] 搜索失败: {e}")
        return f"搜索失败: {str(e)}"


@tool
def generate_from_resume(resume_text: str, focus_area: str = "") -> str:
    """
    根据简历内容生成针对性的面试问题。
    
    Args:
        resume_text: 简历文本内容
        focus_area: 重点关注的方向，如"项目经验"、"技术深度"、"团队协作"等
    
    Returns:
        基于简历生成的面试问题
    """
    focus_hint = f"重点关注：{focus_area}" if focus_area else ""
    
    prompt = f"""你是一个专业的面试官。请根据以下简历内容，生成3个有针对性的面试问题：

简历内容：
{resume_text}

{focus_hint}

请输出3个具体的面试问题，每个问题一行，只输出问题内容，不要编号。
要求：
1. 问题要针对简历中的具体项目或技能
2. 能够考察候选人的真实能力
3. 问题要具体，不要太笼统
"""
    
    try:
        result = openai_llm.invoke(prompt)
        questions = result.content.strip()
        print(f"[generate_from_resume] 生成的问题:\n{questions}")
        return f"【基于简历生成的问题】\n{questions}"
    except Exception as e:
        print(f"[generate_from_resume] 生成失败: {e}")
        return f"生成失败: {str(e)}"


# 导出工具列表
interviewer_tools = [search_interview_questions, generate_from_resume]
