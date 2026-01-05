import os
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv("backend/config/.env")

async def test_llm_thinking():
    print("\n" + "="*60)
    print("纯 LLM 深度思考测试（不使用 Agent）- DeepSeek 版")
    print("="*60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_API_BASE")
    model_name = "deepseek-ai/DeepSeek-V3.2"
    
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
        extra_body={"chat_template_kwargs": {"enable_thinking": True}}

    )
    
    print(f"模型: {model_name}\n")
    print("正在调用 LLM...\n")
    
    # 给一个需要深度推理的问题
    question = """
    有三个候选人：
    1. 张三：5年经验，技能包括 Python, Java, SQL
    2. 李四：3年经验，技能包括 JavaScript, React, Node.js
    3. 王五：4年经验，技能包括 Python, Django, PostgreSQL
    
    现在有一个"高级后端工程师"职位，要求：
    - 至少5年经验
    - 必须掌握 Python 和 Django
    - 熟悉 PostgreSQL 优先
    
    请分析每个候选人的匹配度，并推荐最合适的人选。
    """
    
    response = await llm.ainvoke(question)
    
    content = response.content
    print(content)

if __name__ == "__main__":
    asyncio.run(test_llm_thinking())
