from langchain_core.documents import Document

from backend.graph.rag.service import RagService


class FakeVectorStore:
    def __init__(self, results):
        self.results = results
        self.requested_k = None

    def similarity_search_with_score(self, query, k):
        self.requested_k = k
        return self.results


def test_low_confidence_requests_fallback():
    store = FakeVectorStore([
        (
            Document(
                page_content="过时或不相关的内容",
                metadata={"document_id": "kb-other", "section": "其他"},
            ),
            0.92,
        )
    ])

    result = RagService(store).retrieve("最新政策")

    assert result.confidence == "low"
    assert result.fallback_required is True


def test_retrieved_chunks_keep_source_metadata():
    store = FakeVectorStore([
        (
            Document(
                page_content="STAR：情境、任务、行动、结果。",
                metadata={
                    "document_id": "kb-star",
                    "section": "STAR 法则",
                    "content_hash": "star-hash",
                },
            ),
            0.18,
        )
    ])

    result = RagService(store).retrieve("STAR法则")

    assert result.confidence == "high"
    assert result.documents[0].source.document_id == "kb-star"
    assert result.documents[0].source.section == "STAR 法则"
    assert result.fallback_required is False


def test_duplicate_chunks_are_removed_by_content_hash():
    duplicate = Document(
        page_content="重复内容",
        metadata={"document_id": "kb", "section": "重复", "content_hash": "same"},
    )
    store = FakeVectorStore([(duplicate, 0.2), (duplicate, 0.3)])

    result = RagService(store).retrieve("重复", k=2)

    assert len(result.documents) == 1
    assert store.requested_k == 4
