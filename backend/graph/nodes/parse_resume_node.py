# AI模拟面试系统v1.0，作者刘梦畅
"""
简历解析节点
使用 Agent + 工具自动解析文档（PDF/Word）
"""
import os
from langchain_core.messages import AIMessage
from backend.graph.state import InterviewState
from backend.graph.agents import document_agent


def parse_resume_node(state: InterviewState) -> InterviewState:
    """
    简历解析节点：使用 Agent + 工具自动解析文档（PDF/Word）
    
    Agent 会根据文件扩展名自动选择合适的工具进行解析
    """
    # 如果 resume_text 已经存在，直接返回
    if state.get('resume_text'):
        return state
    
    resume_path = state.get('resume_path', '')
    
    if not resume_path:
        print("[parse_resume_node] 警告: 没有提供简历文件路径")
        return state
    
    if not os.path.exists(resume_path):
        print(f"[parse_resume_node] 警告: 简历文件不存在: {resume_path}")
        return state
        
    # 使用 Agent 解析文档
    try:
        print(f"[parse_resume_node] 开始解析: {resume_path}")
        
        # 调用 Agent 解析
        user_message = f"请解析这个文件：{resume_path}"
        inputs = {
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }
        
        # 使用全局实例化的 document_agent
        result = document_agent.invoke(inputs)
        
        # 从 Agent 响应中提取文本内容
        resume_text = ""
        if result and "messages" in result:
            messages = result["messages"]
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    content = getattr(msg, "content", "")
                    if isinstance(content, str) and content.strip():
                        resume_text = content.strip()
                        break
        
        # 检查解析结果
        if not resume_text or resume_text.startswith("解析失败") or resume_text.startswith("错误"):
            print(f"[parse_resume_node] Agent 返回无效结果: {resume_text}")
            return state
        
        print(f"[parse_resume_node] 解析成功，文本长度: {len(resume_text)}")
        
        # 更新状态
        new_state = state.copy()
        new_state['resume_text'] = resume_text
        return new_state
            
    except Exception as e:
        print(f"[parse_resume_node] 解析简历失败: {e}", exc_info=True)
        raise
