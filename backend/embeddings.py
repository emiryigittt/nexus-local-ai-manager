"""OpenAI-compatible embeddings provided by the selected local runtime."""

from __future__ import annotations

from typing import Any

import httpx

from backend.user_settings import SettingsStore, settings_store


async def embed_texts(
    texts: list[str], store: SettingsStore = settings_store
) -> tuple[list[list[float]], str]:
    preferences = store.load()
    model = preferences.embedding_model.strip()
    provider = store.selected_provider()
    if not texts or not model or provider is None:
        return [], model
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            f"{provider.base_url.rstrip('/')}/embeddings",
            json={"model": model, "input": texts},
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
    rows = sorted(payload.get("data") or [], key=lambda item: item.get("index", 0))
    vectors = [list(map(float, item.get("embedding") or [])) for item in rows]
    if len(vectors) != len(texts) or any(not vector for vector in vectors):
        raise ValueError("The local embedding provider returned an invalid response.")
    return vectors, model
