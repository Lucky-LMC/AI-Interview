# AI智能面试辅助系统V1.0，作者刘梦畅
"""
生成报告节点
使用 LLM 生成面试报告 + 面试教练 Agent 提供学习建议
"""
from langchain_core.messages import HumanMessage
from backend.graph.state import InterviewState
from backend.graph.agents import coach_agent

def generate_report_node(state: InterviewState) -> InterviewState:
    """
    生成最终面试报告：
    1. 使用 LLM 生成基础报告
    2. 使用面试教练 Agent 联网搜索学习资源
    3. 合并成完整报告
    """
    resume_text = state.get('resume_text', '')
    history = state.get('history', [])
    
    if not resume_text or not history:
        print("警告: 简历文本或历史记录为空，无法生成报告")
        return state
    
    try:
        # 构建面试记录文本
        history_text = "\n\n".join([
            f"问题 {i+1}：{h.get('question', '')}\n回答：{h.get('answer', '')}\n反馈：{h.get('feedback', '')}"
            for i, h in enumerate(history)
        ]) if history else "无"
        
        # 构建完整输入信息
        user_message = f"""简历信息：
{resume_text}

面试记录：
{history_text}

请根据以上信息，生成包含综合评价和学习建议的完整面试报告。
注意：针对不足之处，必须使用工具搜索学习资源。"""
        
        print("[generate_report_node] 开始调用这 Coach Agent 生成完整报告...")
        
        # 调用 Coach Agent (现在是全能报告生成 Agent)
        result = coach_agent.invoke({"messages": [HumanMessage(content=user_message)]})
        
        # 提取最终报告
        # ReAct Agent 的最后一条消息内容即为最终输出
        full_report = result["messages"][-1].content
        
        print("[generate_report_node] 完整报告生成完成")
        
        # 更新状态
        new_state = state.copy()
        new_state['report'] = full_report
        return new_state
            
    except Exception as e:
        print(f"[generate_report_node] 生成报告失败: {e}")
        raise

