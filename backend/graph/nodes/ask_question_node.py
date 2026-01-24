# AI智能面试辅助系统V1.0，作者刘梦畅
"""
出题节点
使用面试官 Agent（带工具）智能生成问题
"""
from langchain_core.messages import HumanMessage
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
        
        # 构建 Agent 输入消息
        user_message = f"""当前面试进展：

## 1. 基础信息
- **轮次**: 第 {round_num} / 3 轮
- **候选人岗位**: {target_position}

## 2. 候选人简历
{resume_text}

## 3. 历史问答记录
{history_text}

请根据当前轮次提出下一个面试问题。
**注意**：你必须结合候选人的简历（特别是项目经历）来提问。
**例如**：不要直接问 "什么是 Redis 分布式锁"，而要问 "你在 xx 项目中是如何使用 Redis 实现分布式锁的？"
不要问纯粹的概念定义题。

**注意**：你是面试官，请直接向候选人提问。不要复述简历或历史记录。
"""
        
        print(f"[ask_question_node] 调用面试官 Agent，轮次: {round_num}，岗位: {target_position}")
        
        # 调用 Agent
        agent_input = {"messages": [HumanMessage(content=user_message)]}
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
