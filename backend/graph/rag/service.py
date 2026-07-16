"""Evidence-carrying retrieval with deduplication and fallback decisions."""

import hashlib
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from backend.graph.runtime.contracts import SourceRef


class VectorStore(Protocol):
    def similarity_search_with_score(self, query: str, k: int): ...


class RetrievedChunk(BaseModel):
    content: str
    source: SourceRef
    content_hash: str


class RagResult(BaseModel):
    query: str
    documents: list[RetrievedChunk] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"]
    fallback_required: bool


class RagService:
    def __init__(
        self,
        vectorstore: VectorStore,
        *,
        high_confidence_max_distance: float = 0.35,
        medium_confidence_max_distance: float = 0.60,
    ) -> None:
        self.vectorstore = vectorstore
        self.high_confidence_max_distance = high_confidence_max_distance
        self.medium_confidence_max_distance = medium_confidence_max_distance

    def retrieve(self, query: str, *, k: int = 6) -> RagResult:
        normalized_query = query.strip()
        if not normalized_query:
            return RagResult(
                query=query,
                documents=[],
                confidence="low",
                fallback_required=True,
            )

        candidates = self.vectorstore.similarity_search_with_score(
            normalized_query,
            k=max(k * 2, k),
        )
        deduplicated: dict[str, tuple] = {}
        for document, distance in sorted(candidates, key=lambda item: item[1]):
            content_hash = document.metadata.get("content_hash") or hashlib.sha256(
                document.page_content.encode("utf-8")
            ).hexdigest()
            deduplicated.setdefault(content_hash, (document, float(distance)))
            if len(deduplicated) >= k:
                break

        chunks = [
            RetrievedChunk(
                content=document.page_content,
                content_hash=content_hash,
                source=SourceRef(
                    title=document.metadata.get("section", "面试知识库"),
                    document_id=document.metadata.get("document_id", "interview-knowledge-base"),
                    section=document.metadata.get("section"),
                    score=distance,
                ),
            )
            for content_hash, (document, distance) in deduplicated.items()
        ]

        best_distance = chunks[0].source.score if chunks else None
        if best_distance is not None and best_distance <= self.high_confidence_max_distance:
            confidence = "high"
        elif best_distance is not None and best_distance <= self.medium_confidence_max_distance:
            confidence = "medium"
        else:
            confidence = "low"

        return RagResult(
            query=normalized_query,
            documents=chunks,
            confidence=confidence,
            fallback_required=confidence == "low" or not chunks,
        )
