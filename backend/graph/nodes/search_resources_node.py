# AI智能面试辅助系统V1.0，作者刘梦畅
"""
搜索学习资源节点
调用 Coach Agent 搜索学习资源
"""
from langchain_core.messages import HumanMessage
from backend.graph.state import InterviewState
from backend.graph.agents import coach_agent


def search_resources_node(state: InterviewState) -> InterviewState:
    """
    搜索学习资源节点：
    1. 分析面试记录，提取候选人的主要不足
    2. 调用 Coach Agent 搜索学习资源
    """
    resume_text = state.get('resume_text', '')
    history = state.get('history', [])
    
    if not resume_text or not history:
        print("警告: 简历文本或历史记录为空，跳过搜索")
        new_state = state.copy()
        new_state['learning_resources'] = "无搜索结果"
        return new_state
    
    try:
        # 构建简短的面试记录摘要（只包含问题和回答，不包含反馈）
        qa_summary = "\n".join([
            f"Q{i+1}: {h.get('question', '')}\nA{i+1}: {h.get('answer', '')}"
            for i, h in enumerate(history)
        ])
        
        # 构建简短清晰的任务提示
        user_message = f"""请分析以下面试记录，找出候选人的2-3个主要技术不足，并为每个不足搜索学习资源。

## 候选人简历
{resume_text}

## 面试问答记录
{qa_summary}

## 任务
1. 分析候选人的主要技术不足（2-3个）
2. 对每个不足调用 search_learning_resources 工具搜索学习资源
3. 返回搜索结果

注意：必须调用工具搜索，不要自己编造资源。
"""
        
        print("[search_resources_node] 正在调用 Coach Agent 搜索学习资源...")
        
        # 调用 Agent（输入简短，任务明确）
        result = coach_agent.invoke({"messages": [HumanMessage(content=user_message)]})
        
        # 提取搜索结果
        search_results = result["messages"][-1].content
        
        print(f"[search_resources_node] 搜索完成，结果长度: {len(search_results)}")
        
        # 更新状态
        new_state = state.copy()
        new_state['learning_resources'] = search_results
        return new_state
            
    except Exception as e:
        print(f"[search_resources_node] 搜索失败: {e}")
        new_state = state.copy()
        new_state['learning_resources'] = f"搜索失败: {str(e)}"
        return new_state