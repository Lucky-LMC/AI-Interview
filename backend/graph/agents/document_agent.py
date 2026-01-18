# AI模拟面试系统v1.0，作者刘梦畅
"""
文档解析 Agent
负责根据文件类型调度相应的解析工具
"""
from langgraph.prebuilt import create_react_agent
from backend.graph.llm import get_shared_llm
from backend.graph.tools import pdf_parser_tool, word_parser_tool

# Agent 系统提示词
DOCUMENT_AGENT_PROMPT = """
你是一个专业的文档解析助手。

1. 收到文件路径后，先根据文件扩展名自行判断类型：
   - .pdf → 使用 pdf_parser_tool({"file_path": 路径})
   - .docx/.doc → 使用 word_parser_tool({"file_path": 路径})
2. 如果扩展名不是上述格式，直接说明暂不支持
3. 解析完成后只返回提取的纯文本内容
"""


def create_document_agent():
    """创建文档解析 Agent"""
    if create_react_agent is None:
        raise RuntimeError("请先安装 langgraph: pip install langgraph")
    
    tools = [pdf_parser_tool, word_parser_tool]
    llm = get_shared_llm()
    
    # 使用 langgraph 的 create_react_agent
    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=DOCUMENT_AGENT_PROMPT
    )

# 全局实例化，确保可视化时显示为子图
document_agent = create_document_agent()
