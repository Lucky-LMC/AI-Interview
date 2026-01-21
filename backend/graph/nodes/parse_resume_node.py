# AI智能面试辅助系统V1.0，作者刘梦畅
"""
简历解析节点
直接使用 PDF 解析函数解析简历
"""
import os
from backend.graph.state import InterviewState
from backend.utils.pdf_parser import parse_pdf


def parse_resume_node(state: InterviewState) -> InterviewState:
    """
    简历解析节点：直接解析 PDF 格式简历
    """
    # 如果 resume_text 已经存在，直接返回
    if state.get('resume_text'):
        return state
    
    resume_path = state.get('resume_path', '')
    
    if not resume_path:
        print("[parse_resume_node] 警告: 没有提供简历文件路径")
        return state
    
    if not os.path.exists(resume_path):
        print(f"[parse_resume_node] 警告: 简历文件不存在: {resume_path}")
        return state
        
    # 直接调用 PDF 解析函数
    try:
        print(f"[parse_resume_node] 开始解析: {resume_path}")
        
        resume_text = parse_pdf(resume_path)
        
        # 检查解析结果
        if not resume_text or resume_text.startswith("错误") or resume_text.startswith("警告"):
            print(f"[parse_resume_node] 解析失败: {resume_text}")
            return state
        
        print(f"[parse_resume_node] 解析成功，文本长度: {len(resume_text)}")
        
        # 更新状态
        new_state = state.copy()
        new_state['resume_text'] = resume_text
        return new_state
            
    except Exception as e:
        print(f"[parse_resume_node] 解析简历失败: {e}")
        raise
