"""Version manifest and metadata helpers for reproducible RAG indexes."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.documents import Document
from pydantic import BaseModel, Field


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class RagManifest(BaseModel):
    document_id: str
    content_hash: str
    embedding_model: str
    splitter_version: str
    fingerprint: str
    chunk_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def build_manifest(
    document: str,
    embedding_model: str,
    splitter_version: str,
    *,
    document_id: str = "interview-knowledge-base",
    chunk_count: int = 0,
) -> RagManifest:
    content_hash = _sha256(document)
    fingerprint = _sha256(
        json.dumps(
            {
                "document_id": document_id,
                "content_hash": content_hash,
                "embedding_model": embedding_model,
                "splitter_version": splitter_version,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
    )
    return RagManifest(
        document_id=document_id,
        content_hash=content_hash,
        embedding_model=embedding_model,
        splitter_version=splitter_version,
        fingerprint=fingerprint,
        chunk_count=chunk_count,
    )


def annotate_chunks(documents: list[Document], manifest: RagManifest) -> list[Document]:
    annotated = []
    for index, document in enumerate(documents):
        metadata = dict(document.metadata)
        section = metadata.get("subsection") or metadata.get("section") or "未分类"
        metadata.update(
            document_id=manifest.document_id,
            section=section,
            chunk_index=index,
            content_hash=_sha256(document.page_content),
            embedding_model=manifest.embedding_model,
            splitter_version=manifest.splitter_version,
            manifest_fingerprint=manifest.fingerprint,
        )
        annotated.append(Document(page_content=document.page_content, metadata=metadata))
    return annotated


def write_manifest(path: Path, manifest: RagManifest) -> None:
    path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
