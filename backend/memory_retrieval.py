"""Relevant-memory selection within a fixed prompt budget."""

from __future__ import annotations

import re
from array import array
from datetime import UTC, datetime
from typing import Any

import httpx

from backend.embeddings import embed_texts
from backend.memory import MemoryRepository, memory_repository


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sum(value * value for value in left) ** 0.5
    right_norm = sum(value * value for value in right) ** 0.5
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def _lexical(query: str, content: str) -> float:
    query_tokens = set(re.findall(r"\w+", query.casefold()))
    content_tokens = set(re.findall(r"\w+", content.casefold()))
    return len(query_tokens & content_tokens) / max(1, len(query_tokens | content_tokens))


def rank_memories(
    memories: list[dict[str, Any]],
    query: str,
    *,
    query_vector: list[float] | None = None,
    token_budget: int = 800,
) -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    ranked: list[tuple[float, dict[str, Any]]] = []
    for memory in memories:
        semantic = _lexical(query, str(memory["content"]))
        blob = memory.get("embedding")
        if query_vector and blob:
            vector = array("f")
            vector.frombytes(blob)
            semantic = max(0.0, _cosine(query_vector, list(vector)))
        if semantic < 0.08 and not memory.get("pinned"):
            continue
        try:
            updated = datetime.fromisoformat(str(memory["updated_at"]))
            days = max(0.0, (now - updated).total_seconds() / 86400)
            recency = 1 / (1 + days / 30)
        except (ValueError, TypeError):
            recency = 0.0
        usage = 1.0 if memory.get("last_used_at") else 0.0
        score = (
            semantic * 0.45
            + float(memory.get("importance", 0.5)) * 0.2
            + float(memory.get("confidence", 1.0)) * 0.15
            + recency * 0.1
            + (1.0 if memory.get("pinned") else 0.0) * 0.07
            + usage * 0.03
        )
        ranked.append((score, memory))
    selected: list[dict[str, Any]] = []
    used = 0
    for score, memory in sorted(ranked, key=lambda item: item[0], reverse=True):
        cost = max(8, len(str(memory["content"])) // 4 + 8)
        if used + cost > token_budget:
            continue
        selected.append(memory | {"retrieval_score": round(score, 4)})
        used += cost
    return selected


async def retrieve_memories(
    query: str,
    project_id: str | None,
    *,
    token_budget: int = 800,
    repository: MemoryRepository = memory_repository,
) -> list[dict[str, Any]]:
    memories = repository.for_context(project_id)
    if not memories:
        return []
    query_vector: list[float] | None = None
    try:
        vectors, model = await embed_texts([query])
        if vectors:
            query_vector = vectors[0]
            missing = [item for item in memories if not item.get("embedding") or item.get("embedding_model") != model]
            for offset in range(0, len(missing), 32):
                batch = missing[offset:offset + 32]
                embedded, batch_model = await embed_texts([str(item["content"]) for item in batch])
                if batch_model != model or len(embedded) != len(batch):
                    raise ValueError("Embedding model changed during retrieval.")
                repository.set_embeddings(
                    [(item["id"], vector) for item, vector in zip(batch, embedded, strict=True)], model
                )
            memories = [
                item if item.get("embedding_model") == model else item | {"embedding": None}
                for item in repository.for_context(project_id)
            ]
    except (httpx.HTTPError, ValueError):
        query_vector = None
    selected = rank_memories(
        memories, query, query_vector=query_vector, token_budget=token_budget
    )
    repository.mark_used([item["id"] for item in selected])
    return selected
