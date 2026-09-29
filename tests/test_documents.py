from backend.documents import DocumentRepository


def test_document_index_search_and_delete(tmp_path):
    repository = DocumentRepository(tmp_path / "documents.db")
    document_id = repository.add(
        "privacy.md",
        "Nexus keeps the language model local. Web research requires permission.",
        "markdown",
    )

    results = repository.search("local permission")

    assert results[0]["name"] == "privacy.md"
    assert repository.delete(document_id)
    assert repository.search("local") == []


def test_document_chunking_preserves_overlap():
    chunks = DocumentRepository.chunks("a" * 2000, size=1000, overlap=100)

    assert len(chunks) == 3
    assert chunks[0][-100:] == chunks[1][:100]


def test_semantic_vectors_rank_relevant_chunk(tmp_path):
    repository = DocumentRepository(tmp_path / "vectors.db")
    first = repository.add("first.md", "Local models protect privacy.")
    second = repository.add("second.md", "Cloud services require consent.")
    repository.set_embeddings(first, [[1.0, 0.0]], "local-embed")
    repository.set_embeddings(second, [[0.0, 1.0]], "local-embed")

    results = repository.search(
        "privacy", query_vector=[0.9, 0.1], embedding_model="local-embed"
    )

    assert results[0]["name"] == "first.md"
