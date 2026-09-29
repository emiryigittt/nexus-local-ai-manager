"""Local-model extraction of reviewable memory candidates."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from backend.memory import MEMORY_TYPES, MemoryRepository, memory_repository


class MemoryCandidate(BaseModel):
    content: str = Field(min_length=1, max_length=500)
    key: str = Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9_.-]+$")
    memory_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    importance: float = Field(ge=0.0, le=1.0)
    sensitive: bool = False


MEMORY_RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "nexus_memory_candidates",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "candidates": {
                    "type": "array",
                    "maxItems": 5,
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "key": {"type": "string", "pattern": "^[A-Za-z0-9_.-]+$"},
                            "memory_type": {"enum": sorted(MEMORY_TYPES)},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "importance": {"type": "number", "minimum": 0, "maximum": 1},
                            "sensitive": {"type": "boolean"},
                        },
                        "required": [
                            "content", "key", "memory_type", "confidence", "importance", "sensitive"
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["candidates"],
            "additionalProperties": False,
        },
    },
}


def parse_candidates(content: str, *, strict=False) -> list[MemoryCandidate]:
    try:
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
        payload = json.loads(content)
        values = payload["candidates"]
        if not isinstance(values, list):
            raise ValueError("candidates must be a list")
        candidates = [MemoryCandidate.model_validate(item) for item in values[:5]]
        if any(item.memory_type not in MEMORY_TYPES for item in candidates):
            raise ValueError("Unknown memory type")
    except (ValueError, TypeError, ValidationError, AttributeError, KeyError):
        if strict:
            raise ValueError("Model geçerli hafıza JSON'u döndürmedi.") from None
        return []
    return [item for item in candidates if item.memory_type in MEMORY_TYPES]


SENSITIVE_PATTERNS = (
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"\b(?:api[_ -]?key|access[_ -]?token|bearer|password|parola|şifre)\s*[:=]",
    r"\b(?:sk|pk)-[A-Za-z0-9_-]{16,}\b",
    r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b",
    r"\b(?:tc kimlik|passport|pasaport|social security|ssn)\b",
    r"\b(?:kredi kartı|credit card|cvv|banka hesap|bank account)\b",
    r"\b(?:teşhis|tanı|hastalığım|medication|diagnosis|medical record)\b",
    r"\b(?:ignore|disregard) (?:all )?(?:previous|prior) instructions\b",
    r"\b(?:system prompt|developer message|tool call)\b",
)


def unsafe_for_automatic_memory(content: str) -> bool:
    return any(re.search(pattern, content, flags=re.IGNORECASE) for pattern in SENSITIVE_PATTERNS)


async def learn_from_turn(
    user_text: str,
    assistant_text: str,
    *,
    chat_url: str,
    model: str,
    headers: dict[str, str],
    conversation_id: str | None,
    project_id: str | None,
    repository: MemoryRepository = memory_repository,
    should_save=None,
) -> int:
    prompt = (
        "Extract only durable user preferences, facts, goals, instructions, or project "
        "decisions that would improve future help. Ignore transient requests and assistant "
        "claims. Mark sensitive content. Return the required JSON only.\n\n"
        f"USER:\n{user_text[:6000]}\n\nASSISTANT:\n{assistant_text[:6000]}"
    )
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are Nexus Memory Curator."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "max_tokens": 800,
        "response_format": MEMORY_RESPONSE_SCHEMA,
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(chat_url, json=payload, headers=headers)
        if response.status_code in {400, 422} and any(
            word in response.text.lower() for word in ("response_format", "json_schema", "structured output")
        ):
            # Some local servers do not implement strict structured output.
            # Keep validation strict on our side; never turn free-form text into memory.
            payload.pop("response_format", None)
            payload["messages"][0]["content"] += (
                ' Return ONLY JSON: {"candidates":[{"content":"...","key":"topic.key",'
                '"memory_type":"fact","confidence":0.9,"importance":0.5,"sensitive":false}]}.'
                ' Allowed types: ' + ', '.join(sorted(MEMORY_TYPES)) + '. Use [] for no durable facts.'
            )
            response = await client.post(chat_url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
    choices = result.get("choices") or []
    content = ((choices[0].get("message") or {}).get("content") if choices else "") or ""
    candidates = parse_candidates(str(content), strict=True)
    if should_save is not None and not should_save():
        return 0
    saved = 0
    for candidate in candidates:
        if candidate.sensitive or unsafe_for_automatic_memory(candidate.content):
            continue
        _, outcome = repository.add_candidate(
            candidate.content,
            candidate.memory_type,
            candidate.key,
            project_id=project_id,
            source_conversation_id=conversation_id,
            confidence=candidate.confidence,
            importance=candidate.importance,
        )
        if outcome != "duplicate":
            saved += 1
    return saved
