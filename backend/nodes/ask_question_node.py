# AI模拟面试系统v1.0，作者刘梦畅
"""
出题节点
直接使用 LLM 智能生成问题
"""
from backend.models.state import InterviewState
from .llm_helper import get_shared_llm

# 系统提示词
INTERVIEWER_SYSTEM_PROMPT = """你是一位经验丰富的面试官。

你的任务是进行三轮面试，每轮提出一个有针对性的面试问题。

面试安排：
- 第1轮：通常为技术类问题，考察候选人的技术能力和项目经验
- 第2轮：通常为沟通类问题，考察候选人的沟通能力、团队协作能力
- 第3轮：通常为HR类问题，考察候选人的职业规划、工作态度等

要求：
1. 问题要有针对性，结合简历中的项目经验或技能
2. 难度适中，既考察技术深度又考察实践能力
3. 不要重复之前的问题
4. 根据轮次和候选人的回答情况，灵活选择问题类型
5. 直接输出问题，不要其他内容"""


def ask_question_node(state: InterviewState) -> InterviewState:
    """
    出题节点：直接使用 LLM 智能生成问题
    """
    resume_text = state.get('resume_text', '')
    history = state.get('history', [])
    round_num = state.get('round', 0) + 1
    
    if not resume_text:
        print(f"警告: 没有可用的简历文本用于问题生成 (round={round_num}, history_len={len(history)})")
        return state
    
    # 直接使用 LLM 生成问题
    try:
        llm = get_shared_llm()
        
        # 构建历史问题文本
        history_text = "\n".join([
            f"{i+1}. {h.get('question', '')}" 
            for i, h in enumerate(history)
        ]) if history else "无"
        
        # 构建用户消息
        user_message = f"""简历信息：
{resume_text}

已提问的问题：
{history_text}

请根据简历内容、已提问问题和面试轮次，提出第 {round_num} 个面试问题。"""
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": INTERVIEWER_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        # 调用 LLM
        result = llm.invoke(messages)
        question = result.content.strip()
        
        print(f"[ask_question_node] 生成问题: {question}")
        
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
        print(f"[ask_question_node] 生成问题失败: {e}", exc_info=True)
        raise