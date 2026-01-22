# AI智能面试辅助系统V1.0，作者刘梦畅
"""
生成报告节点
直接使用 LLM 生成最终面试报告
"""
from backend.graph.state import InterviewState
from backend.graph.llm import gemini_llm

# 系统提示词
REPORT_SYSTEM_PROMPT = """你是一位资深的面试官，负责生成最终的面试报告。

你的任务是根据简历信息和完整的面试记录，生成一份 Markdown 格式的综合评价报告：

**面试官**：AI  
**候选人**：[从简历中提取姓名]

### 整体表现总结
[一段话总结候选人的整体表现，包括技术能力、沟通能力、项目经验等方面]

### 优势分析
- 优势点1
- 优势点2
- 优势点3

### 不足之处
- 不足点1
- 不足点2

### 录用建议
**结论**：[推荐/待定/不推荐]  
**理由**：[一句话说明理由]

### 改进方向
- 改进建议1
- 改进建议2
- 改进建议3

**重要格式要求**：
- 使用标准 Markdown 语法
- 列表项紧凑排列，不要空行
- 段落之间用一个空行分隔
- 保持专业客观的评价"""


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
        llm = gemini_llm
        
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
