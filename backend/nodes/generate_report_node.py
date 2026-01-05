# AI模拟面试系统v1.0，作者刘梦畅
"""
生成报告节点
直接使用 LLM 生成最终面试报告
"""
from backend.models.state import InterviewState
from .llm_helper import get_shared_llm

# 系统提示词
REPORT_SYSTEM_PROMPT = """你是一位资深的面试官，负责生成最终的面试报告。

你的任务是根据简历信息和完整的面试记录，生成一份综合评价报告，包括：
开头：面试官：AI，候选人：简历中的姓名
1. 整体表现总结
2. 优势分析
3. 不足之处
4. 录用建议（推荐/待定/不推荐）
5. 改进建议

请生成专业、客观、有建设性的面试报告。"""


def generate_report_node(state: InterviewState) -> InterviewState:
    """
    生成最终面试报告：直接使用 LLM
    """
    resume_text = state.get('resume_text', '')
    history = state.get('history', [])
    
    if not resume_text or not history:
        print("警告: 简历文本或历史记录为空，无法生成报告")
        return state
    
    # 直接使用 LLM 生成报告
    try:
        llm = get_shared_llm()
        
        # 构建面试记录文本
        history_text = "\n\n".join([
            f"问题 {i+1}：{h.get('question', '')}\n回答：{h.get('answer', '')}\n反馈：{h.get('feedback', '')}"
            for i, h in enumerate(history)
        ]) if history else "无"
        
        # 构建用户消息
        user_message = f"""简历信息：
{resume_text}

面试记录：
{history_text}"""
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": REPORT_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        # 调用 LLM
        result = llm.invoke(messages)
        report = result.content.strip()
        
        print(f"[generate_report_node] 生成报告")
        
        # 更新状态
        new_state = state.copy()
        new_state['report'] = report
        return new_state
            
    except Exception as e:
        print(f"[generate_report_node] 生成报告失败: {e}", exc_info=True)
        raise

