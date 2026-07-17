# AI智能面试辅助系统V1.0，作者刘梦畅
"""
RAG 模块
"""
from .init_vectorstore import init_vectorstore

__all__ = ["init_vectorstore"]
from .manifest import RagManifest, annotate_chunks, build_manifest
from .service import RagResult, RagService, RetrievedChunk

__all__ = [
    "RagManifest",
    "RagResult",
    "RagService",
    "RetrievedChunk",
    "annotate_chunks",
    "build_manifest",
]
