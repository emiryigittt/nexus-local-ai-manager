"""Discovery and probing for supported local AI providers."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any

import httpx

from backend.user_settings import ProviderProfile, SettingsStore, settings_store


def _model_ids(payload: dict[str, Any]) -> list[str]:
    values = payload.get("data") or payload.get("models") or []
    models: list[str] = []
    for value in values:
        if isinstance(value, str):
            models.append(value)
        elif isinstance(value, dict):
            identifier = value.get("id") or value.get("name") or value.get("model")
            if identifier:
                models.append(str(identifier))
    return sorted(set(models), key=str.casefold)


async def probe_provider(profile: ProviderProfile, timeout: float = 2.0) -> dict[str, Any]:
    result = asdict(profile)
    result.update({"healthy": False, "models": [], "error": ""})
    try:
        async with httpx.AsyncClient(timeout=timeout, trust_env=False) as client:
            response = await client.get(f"{profile.base_url.rstrip('/')}/models")
            response.raise_for_status()
            models = _model_ids(response.json())
        result.update({"healthy": True, "models": models})
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        result["error"] = str(exc)
    return result


async def discover_providers(store: SettingsStore = settings_store) -> list[dict[str, Any]]:
    profiles = [item for item in store.load().providers if item.enabled]
    if not profiles:
        return []
    return list(await asyncio.gather(*(probe_provider(item) for item in profiles)))


def select_provider(
    provider_id: str,
    model_id: str,
    store: SettingsStore = settings_store,
) -> ProviderProfile:
    preferences = store.load()
    profile = next((item for item in preferences.providers if item.id == provider_id), None)
    if profile is None:
        raise KeyError(provider_id)
    profile.selected_model = model_id
    preferences.selected_provider_id = provider_id
    store.save(preferences)
    return profile
