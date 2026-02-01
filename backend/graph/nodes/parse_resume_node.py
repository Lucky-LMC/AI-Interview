# AI智能面试辅助系统V1.0，作者刘梦畅
"""
简历解析节点
使用 PDF 解析提取原始文本，然后用 LLM 提取关键信息和目标岗位
"""
import os
from backend.graph.state import InterviewState
from backend.utils.pdf_parser import parse_pdf
from backend.graph.llm import openai_llm  # 简历解析不需要工具调用，用 DeepSeek


# LLM 提取简历信息的 Prompt
RESUME_EXTRACT_PROMPT = """你是一个专业的简历分析助手。请从以下简历内容中提取关键信息，并以 Markdown 格式输出。

## 简历原文：
{resume_raw_text}

## 请按以下 Markdown 格式提取信息：

### 目标岗位
[从简历中识别目标岗位。必须输出具体的岗位名称，如"Java开发工程师"、"Python后端工程师"、"前端开发工程师"等。**严禁输出"未提及"、"未识别"或其他非岗位内容**。如简历未明确写明，请根据技能栈、项目经验智能推断。只输出岗位名称本身，不要添加任何前缀、后缀或解释性文字。]

**正确示例**：
- Java开发工程师
- Python后端工程师
- 前端开发工程师

**错误示例（禁止）**：
- 目标岗位：Java开发工程师（多余前缀）
- Java开发工程师（全栈方向）（多余后缀）
- 未提及（禁止）
- 未识别（禁止）

### 个人信息
- **姓名**：[姓名]
- **学历**：[学历]
- **工作年限**：[年限]

### 核心技能
- 技能1
- 技能2
- 技能3
- 技能xxxx

### 项目经历亮点
- 项目1：[简要描述]
- 项目2：[简要描述]
- 项目xxxx

### 面试关注点
- 关注点1
- 关注点2
- 关注点xxxx

**格式要求**：
- 使用标准 Markdown 语法
- 列表项紧凑排列，不要空行
- 信息简洁准确
- 除"目标岗位"外，未提及的信息可标注"未提及"
"""


def parse_resume_node(state: InterviewState) -> InterviewState:
    """
    简历解析节点：
    1. 解析 PDF 获取原始文本
    2. 使用 LLM 提取关键信息和目标岗位
    """
    # 如果 resume_text 已经存在，直接返回
    if state.get('resume_text') and state.get('target_position'):
        return state
    
    resume_path = state.get('resume_path', '')
    
    if not resume_path:
        print("[parse_resume_node] 警告: 没有提供简历文件路径")
        return state
    
    if not os.path.exists(resume_path):
        print(f"[parse_resume_node] 警告: 简历文件不存在: {resume_path}")
        return state
        
    try:
        # ========== 步骤1：解析 PDF 获取原始文本 ==========
        print(f"[parse_resume_node] 开始解析PDF: {resume_path}")
        
        resume_raw_text = parse_pdf(resume_path)
        
        # 检查解析结果
        if not resume_raw_text or resume_raw_text.startswith("错误") or resume_raw_text.startswith("警告"):
            print(f"[parse_resume_node] PDF解析失败: {resume_raw_text}")
            return state
        
        print(f"[parse_resume_node] PDF解析成功，原始文本长度: {len(resume_raw_text)}")
        
        # ========== 步骤2：使用 LLM 提取关键信息 ==========
        print("[parse_resume_node] 正在使用LLM提取简历信息...")
        
        # 构建 prompt
        prompt = RESUME_EXTRACT_PROMPT.format(resume_raw_text=resume_raw_text)
        
        # 调用 LLM
        response = openai_llm.invoke(prompt)
        extracted_info = response.content
        
        print(f"[parse_resume_node] LLM提取完成，信息长度: {len(extracted_info)}")
        
        # ========== 步骤3：从提取结果中解析目标岗位 ==========
        target_position = "未识别"
        
        # 尝试从 LLM 输出中提取目标岗位
        if "### 目标岗位" in extracted_info:
            lines = extracted_info.split("\n")
            for i, line in enumerate(lines):
                if "### 目标岗位" in line:
                    # 获取下一行作为目标岗位
                    if i + 1 < len(lines):
                        position_line = lines[i + 1].strip()
                        if position_line and not position_line.startswith("#"):
                            # 移除可能的 Markdown 列表符号（- , * , 数字.）
                            position_line = position_line.lstrip('- *')  # 移除列表符号
                            position_line = position_line.strip()  # 再次去除空格
                            # 移除数字编号
                            import re
                            position_line = re.sub(r'^\d+\.\s*', '', position_line)
                            target_position = position_line
                    break
        
        print(f"[parse_resume_node] 提取的目标岗位: {target_position}")
        
        # ========== 步骤4：更新状态 ==========
        new_state = state.copy()
        new_state['resume_text'] = extracted_info  # LLM 提取的结构化信息
        new_state['target_position'] = target_position
        
        return new_state
            
    except Exception as e:
        print(f"[parse_resume_node] 解析简历失败: {e}")
        raise
