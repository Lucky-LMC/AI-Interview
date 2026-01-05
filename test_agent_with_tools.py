import os
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv("backend/config/.env")

@tool
def get_weather(city: str):
    """获取指定城市的实时天气"""
    return f"{city}今天晴，25度。"

async def test_agent_with_tools():
    print("\n" + "="*60)
    print("3. Agent 包装测试 (带工具, Kimi-Dev-72B)")
    print("="*60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE")
    model_name = "moonshotai/Kimi-Dev-72B"
    
    llm = ChatOpenAI(
        model=model_name,
        base_url=base_url,
        api_key=api_key,
        temperature=0.7,
        extra_body={"chat_template_kwargs": {"enable_thinking": True}}
    )
    
    # 创建 Agent，提供工具
    agent = create_react_agent(llm, tools=[get_weather], prompt="你是一个助手。")
    
    inputs = {"messages": [("user", "北京天气怎么样？")]}
    
    print(f"正在运行 Agent: {model_name}...")
    result = await agent.ainvoke(inputs)
    
    print("\n" + "="*40)
    print("消息流分析:")
    print("="*40)
    
    for msg in result["messages"]:
        print(f"\n【{msg.type.upper()}】:")
        content = msg.content
        if "</think>" in content:
            parts = content.split("</think>")
            thinking = parts[0].replace("<think>", "").strip()
            answer = parts[1].strip()
            print(f"🧠 思考: {thinking[:200]}...")
            print(f"💬 回复: {answer}")
        else:
            print(content)
        
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print(f"🛠️ 工具调用: {msg.tool_calls[0]['name']}")

if __name__ == "__main__":
    asyncio.run(test_agent_with_tools())
