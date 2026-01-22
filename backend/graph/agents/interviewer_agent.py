# AI智能面试辅助系统V1.0，作者刘梦畅
"""
面试官 Agent 定义
使用 ReAct 模式，可以调用工具进行出题
支持流式输出（打字机效果）
"""
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from backend.graph.llm import openai_llm
from backend.graph.tools import interviewer_tools


# Agent 系统提示词
INTERVIEWER_AGENT_PROMPT = """你是一位经验丰富的面试官 Agent。

你的任务是为候选人提出高质量的面试问题。你有两个工具可以使用：

1. **search_interview_questions**: 根据候选人的目标岗位，联网搜索该岗位的常见面试题目
2. **generate_from_resume**: 根据候选人的简历内容，生成针对性的面试问题

## 出题策略：

根据面试轮次选择合适的工具和策略：

- **第1轮（技术类）**: 
  - 优先使用 generate_from_resume 工具，针对简历中的项目经验深挖
  - 可以结合 search_interview_questions 搜索该岗位的技术面试题

- **第2轮（沟通类）**: 
  - 使用 search_interview_questions 搜索沟通类、团队协作类问题
  - 结合简历中的团队项目经历提问

- **第3轮（HR类）**: 
  - 使用 search_interview_questions 搜索 HR 类问题
  - 关注职业规划、工作态度等软性问题

## 输出要求：

1. 调用工具获取候选问题后，从中选择最合适的一个问题
2. 最终只输出一个问题，不要输出其他内容
3. 问题要具体、有深度，能考察候选人的真实能力
4. 不要重复之前已经问过的问题
"""


def create_interviewer_agent():
    """
    创建面试官 Agent
    
    使用 LangGraph 的 create_react_agent 创建一个可以调用工具的 Agent
    返回的是一个 CompiledGraph，可以直接作为子图使用
    """
    agent = create_react_agent(
        model=openai_llm,
        tools=interviewer_tools,
        prompt=INTERVIEWER_AGENT_PROMPT
    )
    return agent


# 创建全局 Agent 实例
# 这个实例可以直接作为子图嵌入到主工作流中
interviewer_agent = create_interviewer_agent()
