from backend.graph.rag.manifest import build_manifest


def test_manifest_changes_when_embedding_model_changes():
    document = "# 面试知识库\nSTAR 法则"

    first = build_manifest(document, "BAAI/bge-m3", "headers-v1")
    second = build_manifest(document, "other-model", "headers-v1")

    assert first.fingerprint != second.fingerprint
    assert first.content_hash == second.content_hash


def test_manifest_is_stable_for_same_inputs():
    first = build_manifest("same", "embedding", "splitter-v1")
    second = build_manifest("same", "embedding", "splitter-v1")

    assert first.fingerprint == second.fingerprint
