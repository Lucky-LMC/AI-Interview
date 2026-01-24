# AI智能面试辅助系统V1.0，作者刘梦畅
"""
生成报告节点
使用面试教练 Agent 生成包含简历诊断和学习建议的完整报告
"""
from langchain_core.messages import HumanMessage
from backend.graph.state import InterviewState
from backend.graph.agents import coach_agent

def generate_report_node(state: InterviewState) -> InterviewState:
    """
    生成最终面试报告：
    调用 Coach Agent，它会负责：
    1. 简历诊断
    2. 联网搜索学习资源
    3. 生成完整 Markdown 报告
    """
    resume_text = state.get('resume_text', '')
    history = state.get('history', [])
    
    if not resume_text or not history:
        print("警告: 简历文本或历史记录为空，无法生成报告")
        return state
    
    try:
        # 1. 准备完整的面试记录（不截断）
        history_text = "\n\n".join([
            f"问题 {i+1}：{h.get('question', '')}\n回答：{h.get('answer', '')}\n反馈：{h.get('feedback', '')}"
            for i, h in enumerate(history)
        ]) if history else "无"
        
        # 2. 构建输入消息
        user_message = f"""请生成面试报告。

## 候选人档案
{resume_text}

## 完整面试记录
{history_text}

## 任务要求
1. **简历诊断**：指出简历问题并给出修改建议。
2. **学习建议**：针对不足，**必须调用工具**搜索真实书籍/课程。
3. **输出格式**：直接输出 Markdown，不要代码块。
"""
        
        print("[generate_report_node] 正在调用 Coach Agent (简历诊断+搜索+报告)...")
        
        # 3. 调用 Agent
        # Agent 内部会根据 Prompt 执行 ReAct 循环（思考 -> 搜工具 -> 写报告）
        result = coach_agent.invoke({"messages": [HumanMessage(content=user_message)]})
        
        # 4. 提取最终结果
        full_report = result["messages"][-1].content
        
        print(f"[generate_report_node] Agent 任务完成，报告长度: {len(full_report)}")
        
        # 5. 更新状态
        new_state = state.copy()
        new_state['report'] = full_report
        return new_state
            
    except Exception as e:
        print(f"[generate_report_node] Agent 调用失败: {e}")
        # 兜底：如果 Agent 挂了，至少不让程序崩溃，返回一个简单的错误提示
        new_state = state.copy()
        new_state['report'] = f"# 生成报告失败\n\n系统错误: {str(e)}"
        return new_state

