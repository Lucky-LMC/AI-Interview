# AI智能面试辅助系统V1.0，作者刘梦畅
"""
PDF 解析模块
提供 PDF 文件的文本提取功能
"""
import os

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None


def parse_pdf(file_path: str) -> str:
    """
    解析 PDF 文件并提取文本内容
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 提取的文本内容，如果失败返回错误信息
    """
    if PyPDF2 is None:
        return "错误：请先安装 PyPDF2: pip install PyPDF2"
    
    if not file_path:
        return "错误：未提供文件路径"
    
    if not os.path.exists(file_path):
        return f"错误：文件不存在 - {file_path}"
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # 提取所有页面的文本
            text_content = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
            
            # 合并所有文本
            full_text = "\n".join(text_content)
            
            if full_text:
                return full_text.strip()
            else:
                return "警告：PDF 文件为空或无法提取文本"
            
    except Exception as e:
        print(f"PDF 解析错误: {str(e)}")
        return f"错误：PDF 解析失败 - {str(e)}"
