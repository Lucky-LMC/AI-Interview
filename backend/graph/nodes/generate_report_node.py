# AI智能面试辅助系统V1.0，作者刘梦畅
"""
生成最终报告节点
整合所有信息生成完整的面试报告
"""
from backend.graph.state import InterviewState
from backend.graph.llm import openai_llm


def generate_report_node(state: InterviewState) -> InterviewState:
    """
    生成最终面试报告：
    整合简历、面试记录、学习资源，生成完整报告
    """
    resume_text = state.get('resume_text', '')
    history = state.get('history', [])
    learning_resources = state.get('learning_resources', '')
    
    if not resume_text or not history:
        print("警告: 简历文本或历史记录为空，无法生成报告")
        return state
    
    try:
        # 准备完整的面试记录
        history_text = "\n\n".join([
            f"**问题 {i+1}**：{h.get('question', '')}\n**回答**：{h.get('answer', '')}\n**反馈**：{h.get('feedback', '')}"
            for i, h in enumerate(history)
        ])
        
        # 构建报告生成提示词
        prompt = f"""你是一位资深面试官，请根据以下信息生成一份完整的面试报告。

## 候选人简历
{resume_text}

## 完整面试记录
{history_text}

## 学习资源推荐（已搜索，包含链接）
{learning_resources}

## 报告要求
请按照以下 Markdown 格式输出完整报告：

### 📊 整体表现总结
[一段话总结候选人的整体表现，涵盖技术能力、沟通表达、项目经验等方面]

### ✅ 优势分析
- [优势1：具体说明]
- [优势2：具体说明]
- [优势3：具体说明]

### ⚠️ 不足与改进建议
#### 1. [不足领域1]
- **问题分析**：[具体说明哪里表现不足]
- **提升建议**：
  [从上面的学习资源中提取对应的内容，**必须保留 Markdown 链接格式 `[标题](URL)`**]

#### 2. [不足领域2]
- **问题分析**：[具体说明]
- **提升建议**：
  [对应的学习资源，**保留链接格式**]

### 📝 简历优化建议
- **[简历问题点1]**：
  - *问题分析*：[对比面试表现，指出简历中的问题，如：描述空洞、未体现技术深度等]
  - *修改建议*：[给出具体的修改方向或示例文案]
- **[简历问题点2]**：
  - *问题分析*：[...]
  - *修改建议*：[...]

### 🎯 录用建议
**结论**：[推荐/待定/不推荐]  
**理由**：[综合评价，给出明确理由]

---
**重要提醒**：
1. 直接输出 Markdown 格式，不要用代码块包裹
2. 学习资源部分**必须保留原始的 Markdown 链接格式 `[标题](URL)`**，不要转换成纯文本
3. 直接复制粘贴学习资源中的链接，不要自己编造
4. 简历优化要结合面试表现，指出简历与实际能力的差距
"""
        
        print("[generate_report_node] 正在生成最终报告...")
        
        # 调用 LLM 生成报告
        response = openai_llm.invoke(prompt)
        full_report = response.content
        
        print(f"[generate_report_node] 报告生成完成，长度: {len(full_report)}")
        
        # 更新状态
        new_state = state.copy()
        new_state['report'] = full_report
        return new_state
            
    except Exception as e:
        print(f"[generate_report_node] 报告生成失败: {e}")
        new_state = state.copy()
        new_state['report'] = f"# 生成报告失败\n\n系统错误: {str(e)}"
        return new_state

