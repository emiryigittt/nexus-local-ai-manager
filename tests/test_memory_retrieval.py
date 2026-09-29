from datetime import UTC, datetime

import pytest

from backend.memory import MemoryRepository
from backend.memory_retrieval import rank_memories


def test_memory_ranking_respects_relevance_and_token_budget():
    now = datetime.now(UTC).isoformat()
    memories = [
        {
            "id": "python",
            "content": "Kullanıcı Python ve pytest kullanıyor",
            "importance": 0.8,
            "confidence": 1.0,
            "pinned": 0,
            "updated_at": now,
            "last_used_at": None,
        },
        {
            "id": "food",
            "content": "Kullanıcı acılı yemek seviyor",
            "importance": 0.5,
            "confidence": 1.0,
            "pinned": 0,
            "updated_at": now,
            "last_used_at": None,
        },
    ]

    selected = rank_memories(memories, "Python testi yaz", token_budget=20)

    assert [item["id"] for item in selected] == ["python"]


@pytest.mark.asyncio
async def test_retrieval_reuses_embeddings_and_refreshes_edited_memory(tmp_path, monkeypatch):
    from backend.memory_retrieval import retrieve_memories

    repository = MemoryRepository(tmp_path / "memory.db")
    identifier = repository.add("Python kullanır", "fact")
    calls = []

    async def embed(texts):
        calls.append(texts)
        return [[1.0, 0.0] for text in texts], "local-embed"

    monkeypatch.setattr("backend.memory_retrieval.embed_texts", embed)
    await retrieve_memories("Python", None, repository=repository)
    await retrieve_memories("Python", None, repository=repository)
    assert calls == [["Python"], ["Python kullanır"], ["Python"]]
    repository.update(identifier, "Rust kullanır")
    await retrieve_memories("Rust", None, repository=repository)
    assert calls[-2:] == [["Rust"], ["Rust kullanır"]]


@pytest.mark.asyncio
async def test_embedding_failure_uses_lexical_memory_search(tmp_path, monkeypatch):
    from backend.memory_retrieval import retrieve_memories

    repository = MemoryRepository(tmp_path / "memory.db")
    repository.add("Python kullanır", "fact")

    async def unavailable(texts):
        raise ValueError("embedding unavailable")

    monkeypatch.setattr("backend.memory_retrieval.embed_texts", unavailable)
    result = await retrieve_memories("Python", None, repository=repository)
    assert result[0]["content"] == "Python kullanır"
