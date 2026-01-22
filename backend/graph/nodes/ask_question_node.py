# AI智能面试辅助系统V1.0，作者刘梦畅
"""
出题节点
使用面试官 Agent（带工具）智能生成问题
"""
from backend.graph.state import InterviewState
from backend.graph.agents import interviewer_agent




def ask_question_node(state: InterviewState) -> InterviewState:
    """
    出题节点：使用面试官 Agent 智能生成问题
    
    Agent 会根据情况选择：
    1. 联网搜索该岗位的面试题
    2. 根据简历生成针对性问题
    """
    resume_text = state.get('resume_text', '')
    target_position = state.get('target_position', '未知岗位')
    history = state.get('history', [])
    round_num = state.get('round', 0) + 1
    
    if not resume_text:
        print(f"[ask_question_node] 警告: 没有可用的简历文本 (round={round_num})")
        return state
    
    try:
        # 构建历史问题文本
        history_text = "\n".join([
            f"{i+1}. {h.get('question', '')}" 
            for i, h in enumerate(history)
        ]) if history else "无"
        
        # 确定当前轮次的问题类型
        question_types = {1: "技术", 2: "沟通", 3: "HR"}
        question_type = question_types.get(round_num, "综合")
        
        # 构建 Agent 输入消息
        user_message = f"""请为以下候选人生成第 {round_num} 轮面试问题。

## 候选人信息
- 目标岗位：{target_position}
- 当前轮次：第 {round_num} 轮（{question_type}类问题）

## 简历摘要
{resume_text}

## 已提问的问题
{history_text}

请使用你的工具获取候选问题，然后选择最合适的一个问题输出。
注意：不要重复已提问的问题，直接输出最终选定的问题即可。
"""
        
        print(f"[ask_question_node] 调用面试官 Agent，轮次: {round_num}，岗位: {target_position}")
        
        # 调用 Agent
        agent_input = {"messages": [{"role": "user", "content": user_message}]}
        result = interviewer_agent.invoke(agent_input)
        
        # 从 Agent 输出中提取最终问题
        # Agent 的输出格式是 {"messages": [...]}
        messages = result.get("messages", [])
        question = ""
        
        # 获取最后一条 AI 消息作为问题
        for msg in reversed(messages):
            if hasattr(msg, 'content') and msg.content:
                # 跳过工具调用消息
                if not hasattr(msg, 'tool_calls') or not msg.tool_calls:
                    question = msg.content.strip()
                    break
        
        if not question:
            # 如果没有获取到问题，使用备用逻辑
            question = f"请介绍一下你在{target_position}相关领域的工作经验和技能。"
        
        print(f"[ask_question_node] 生成的问题: {question}")
        
        # 将问题添加到历史记录
        history_entry = {
            "question": question,
            "answer": "",
            "feedback": ""
        }
        
        new_history = state.get('history', []).copy()
        new_history.append(history_entry)
        
        # 更新状态
        new_state = state.copy()
        new_state['history'] = new_history
        return new_state
            
    except Exception as e:
        import traceback
        print(f"[ask_question_node] Agent 调用失败: {e}")
        print(traceback.format_exc())
        # 降级处理：使用简单问题
        fallback_question = f"请介绍一下你最擅长的技术领域，并举例说明在项目中的应用。"
        
        history_entry = {
            "question": fallback_question,
            "answer": "",
            "feedback": ""
        }
        
        new_history = state.get('history', []).copy()
        new_history.append(history_entry)
        
        new_state = state.copy()
        new_state['history'] = new_history
        return new_state
