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
# Agent 系统提示词
INTERVIEWER_AGENT_PROMPT = """你是一位资深技术面试官。

## 🛑 核心指令
**必须先调研，后发言。**
在提出任何面试问题之前，你**必须**先调用 `search_interview_questions(topic)` 工具获取最新的面试题库，然后再结合简历进行定制。

## 💡 示例流程（请模仿此行为）

**User**: "请开始第 1 轮面试，岗位是 Java后端。"

**Assistant**: 
*(思考: 我需要先了解 Java 后端最新的面试热点)*
**[调用工具]** search_interview_questions("Java后端 2025 面试题")
(...工具返回结果...)
*(思考: 搜索结果提到了 Redis，候选人简历里也有 Redis 项目)*
**[最终回答]**: "我看你在项目中使用了 Redis，请问你是如何处理 Redis 缓存穿透问题的？"

---

## ⚠️ 执行要求
1. **这是强制的**：每一轮都必须且只能调用一次工具。
2. **灵活搜索**：根据简历内容，灵活决定搜什么 topic（如 "Spring Cloud"、"高并发设计"）。
3. **最终输出**：只输出一个问题，不要输出思考过程。
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
