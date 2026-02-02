# AI智能面试辅助系统V1.0，作者刘梦畅
"""
向量数据库初始化脚本
将面试知识库文档向量化并存储到 Chroma
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_chroma import Chroma
from backend.graph.llm import openai_embeddings
from backend.config import EMBEDDING_MODEL

# 知识库文件路径
KNOWLEDGE_BASE_PATH = Path(__file__).parent / "interview_knowledge_base.md"
# Chroma 数据库存储路径
CHROMA_DB_PATH = Path(__file__).parent / "chroma_db"


def init_vectorstore():
    """
    初始化向量数据库
    1. 读取知识库文档
    2. 按 Markdown 标题切分
    3. 向量化并存储到 Chroma
    """
    print("=" * 60)
    print("开始初始化向量数据库...")
    print("=" * 60)
    
    # 1. 读取知识库文档
    print(f"\n[1/4] 读取知识库文档: {KNOWLEDGE_BASE_PATH}")
    if not KNOWLEDGE_BASE_PATH.exists():
        raise FileNotFoundError(f"知识库文件不存在: {KNOWLEDGE_BASE_PATH}")
    
    with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
        markdown_text = f.read()
    
    print(f"  ✓ 文档大小: {len(markdown_text)} 字符")
    
    # 2. 按 Markdown 标题切分文档
    print("\n[2/4] 切分文档...")
    headers_to_split_on = [
        ("##", "section"),      # 二级标题（模块）
        ("###", "subsection"),  # 三级标题（知识点）
    ]
    
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    
    docs = markdown_splitter.split_text(markdown_text)
    print(f"  ✓ 切分为 {len(docs)} 个文档块")
    
    # 3. 使用全局 Embedding 模型
    print("\n[3/4] 使用 Embedding 模型...")
    print(f"  ✓ 使用模型: {EMBEDDING_MODEL}")
    
    # 4. 创建/更新向量数据库
    print(f"\n[4/4] 创建向量数据库: {CHROMA_DB_PATH}")
    
    if CHROMA_DB_PATH.exists():
        print("  ✓ 检测到已有数据库，删除旧 collection 并重建")
        # 先加载现有数据库
        try:
            client = Chroma(
                persist_directory=str(CHROMA_DB_PATH),
                embedding_function=openai_embeddings
            )
            # 删除旧的 collection
            client.delete_collection()
            print("  ✓ 旧 collection 已删除")
        except:
            # 如果删除失败（可能不存在），忽略错误
            pass
    
    # 创建新数据库
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=openai_embeddings,
        persist_directory=str(CHROMA_DB_PATH),
        collection_name="interview_knowledge"
    )
    
    print(f"  ✓ 向量数据库创建成功，共 {len(docs)} 个文档")
    
    # 5. 测试检索
    print("\n" + "=" * 60)
    print("测试向量检索...")
    print("=" * 60)
    
    test_queries = [
        "简历怎么写",
        "如何谈薪资",
        "STAR法则是什么",
        "面试紧张怎么办"
    ]
    
    for query in test_queries:
        results = vectorstore.similarity_search(query, k=1)
        if results:
            print(f"\n查询: {query}")
            print(f"结果: {results[0].page_content[:100]}...")
    
    print("\n" + "=" * 60)
    print("✅ 向量数据库初始化完成！")
    print("=" * 60)
    
    return vectorstore


if __name__ == "__main__":
    init_vectorstore()
