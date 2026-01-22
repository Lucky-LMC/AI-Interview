# AI智能面试辅助系统V1.0，作者刘梦畅
"""
评价节点
直接使用 LLM 对回答进行评价并生成反馈
"""
from backend.graph.state import InterviewState
from backend.graph.llm import gemini_llm

# 系统提示词
EVALUATOR_SYSTEM_PROMPT = """你是一位专业的技术面试官，负责对面试回答进行评价并生成反馈。

你的任务是对候选人的回答进行多维度评分和给出评价，必须严格按照 Markdown 格式输出：

### 综合评价
1. **技术准确性** (X/5)：评价内容
2. **回答完整性** (X/5)：评价内容
3. **表达清晰度** (X/5)：评价内容
4. **实践经验体现** (X/5)：评价内容

### 改进建议
- 建议1
- 建议2
- 建议3

**重要格式要求**：
- 使用标准 Markdown 语法
- 列表项紧凑排列，不要空行
- 每个评分项占一行
- 直接输出内容，不要开场白或结束语"""


def evaluate_node(state: InterviewState) -> InterviewState:
    """
    评价节点：直接使用 LLM 对回答进行评价并生成反馈
    """
    history = state.get('history', [])
    
    if not history:
        print("警告: 历史记录为空，无法生成反馈")
        return state
    
    # 从历史记录的最后一条获取问题和答案
    last_entry = history[-1]
    question = last_entry.get('question', '')
    answer = last_entry.get('answer', '')
    
    if not question or not answer:
        print("警告: 问题或回答为空，无法生成反馈")
        return state

    # 直接使用 LLM 生成反馈
    try:
        llm = gemini_llm
        
        # 构建用户消息
        user_message = f"""问题：{question}

回答：{answer}

请对以上回答进行评分和给出评价。"""
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
        
        # 调用 LLM
        result = llm.invoke(messages)
        feedback = result.content.strip()
        
        print(f"[evaluate_node] 生成反馈")
        
        # 更新历史记录
        new_history = state['history'].copy()
        new_history[-1]['feedback'] = feedback
        
        # 更新状态
        new_state = state.copy()
        new_state['history'] = new_history
        new_state['round'] = state['round'] + 1
        return new_state
            
    except Exception as e:
        print(f"[evaluate_node] 生成反馈失败: {e}", exc_info=True)
        raise
