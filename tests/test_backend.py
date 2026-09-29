import pytest
from fastapi import HTTPException

from backend.main import (
    ChatRequest,
    _build_prompt,
    _clean_model_output,
    _schedule_memory_learning,
    _schedule_summary_updates,
    _stream_event,
)
from backend.user_settings import UserPreferences


def test_clean_model_output_removes_hidden_reasoning():
    result = {
        "choices": [
            {"message": {"content": "<think>private chain</think>\nFinal answer"}}
        ]
    }

    assert _clean_model_output(result) == "Final answer"


def test_clean_model_output_rejects_reasoning_only_response():
    result = {"choices": [{"message": {"content": "", "reasoning_content": "Answer"}}]}

    with pytest.raises(HTTPException, match="empty response"):
        _clean_model_output(result)


def test_clean_model_output_rejects_empty_choices():
    with pytest.raises(HTTPException) as exc_info:
        _clean_model_output({"choices": []})

    assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_build_prompt_rejects_empty_request():
    with pytest.raises(HTTPException) as exc_info:
        await _build_prompt(ChatRequest())

    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_build_prompt_creates_multimodal_content():
    content, system = await _build_prompt(ChatRequest(text="What is this?", image="abc"))

    assert content[0] == {"type": "text", "text": "What is this?"}
    assert content[1]["image_url"]["url"] == "data:image/jpeg;base64,abc"
    assert "multimodal" in system


def test_stream_event_preserves_unicode_content():
    event = _stream_event("chunk", text="Türkçe yanıt")

    assert event == '{"event": "chunk", "text": "Türkçe yanıt"}\n'


@pytest.mark.asyncio
async def test_build_prompt_metadata_shape_is_backward_compatible():
    content, system, sources = await _build_prompt(
        ChatRequest(text="Merhaba", private=True), include_metadata=True
    )

    assert content == "Merhaba"
    assert "Nexus" in system
    assert sources == []


@pytest.mark.asyncio
async def test_private_session_bypasses_memory_summaries_and_embeddings(monkeypatch):
    preferences = UserPreferences.defaults()
    preferences.memory_enabled = True
    preferences.memory_auto_learn = True
    preferences.memory_reference_history = True
    monkeypatch.setattr("backend.main.settings_store.load", lambda: preferences)

    async def forbidden_retrieval(*args, **kwargs):
        raise AssertionError("Private session must not retrieve or embed memories")

    monkeypatch.setattr("backend.main.retrieve_memories", forbidden_retrieval)
    request = ChatRequest(text="Gizli konuşma", private=True, conversation_id="private")

    content, _ = await _build_prompt(request)
    _schedule_memory_learning(request, "Yanıt")
    _schedule_summary_updates(request, "Yanıt")

    assert content == "Gizli konuşma"
