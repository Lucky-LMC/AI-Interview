import os
import asyncio
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

load_dotenv("backend/config/.env")

async def test_agent_no_tools():
    print("\n" + "="*60)
    print("2. Agent 包装测试 (无工具, Kimi-Dev-72B)")
    print("="*60)
    
    api_key = "ms-e714a9a5-5652-47f2-8d94-8459a6152b59"
    model_name = "deepseek-ai/DeepSeek-R1-Distill-Llama-8B"
    base_url = "https://api-inference.modelscope.cn/v1"
    
    llm = ChatOpenAI(
        model=model_name,
        base_url=base_url,
        api_key=api_key,
        temperature=0.7,
        extra_body={"chat_template_kwargs": {"enable_thinking": True}}
    )
    
    # 创建 Agent，不提供工具
    agent = create_react_agent(llm, tools=[], prompt="你是一个专业的面试官。")
    
    inputs = {"messages": [("user", "作为高级后端工程师，你最看重候选人的哪些素质？")]}
    
    print(f"正在运行 Agent: {model_name}...")
    result = await agent.ainvoke(inputs)
    
    # 获取最后一条 AI 消息
    last_msg = result["messages"][-1]
    content = last_msg.content
    
    if "</think>" in content:
        parts = content.split("</think>")
        thinking = parts[0].replace("<think>", "").strip()
        answer = parts[1].strip()
        print("\n🧠 【Agent 内部思考】:")
        print("-" * 40)
        print(thinking)
        print("\n💬 【Agent 最终回复】:")
        print("-" * 40)
        print(answer)
    else:
        print("\n💬 【Agent 回复】:")
        print("-" * 40)
        print(content)

if __name__ == "__main__":
    asyncio.run(test_agent_no_tools())
