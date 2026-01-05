# AI模拟面试系统v1.0，作者刘梦畅
"""
评价节点
直接使用 LLM 对回答进行评价并生成反馈
"""
from backend.models.state import InterviewState
from .llm_helper import get_shared_llm

# 系统提示词
EVALUATOR_SYSTEM_PROMPT = """你是一位专业的技术面试官，负责对面试回答进行评价并生成反馈。

你的任务是对候选人的回答进行多维度评分和给出评价，必须严格按照以下格式输出：

### 综合评价

1. **技术准确性**：
   - 评分：X/5（1-5分）
   - 评价：详细评价候选人的技术回答是否准确，技术点是否正确，是否有技术错误等。

2. **回答完整性**：
   - 评分：X/5（1-5分）
   - 评价：详细评价回答是否完整，是否涵盖了问题的各个方面，是否遗漏了重要信息等。

3. **表达清晰度**：
   - 评分：X/5（1-5分）
   - 评价：详细评价回答的表达是否清晰，逻辑是否清楚，语言是否专业等。

4. **实践经验体现**：
   - 评分：X/5（1-5分）
   - 评价：详细评价回答中是否体现了实际项目经验，是否展示了解决问题的能力，是否有具体的实践案例等。

### 改进建议
根据综合评价，给出详细具体的改进建议，必要时可以给一些具体的例子。

请严格按照以上格式输出，直接输出反馈内容，不要包含其他开场白或结束语。"""


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
        llm = get_shared_llm()
        
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