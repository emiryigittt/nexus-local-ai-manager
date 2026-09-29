import json

import httpx
import pytest

from backend import main
from backend.chat_context import MAX_CONTEXT_CHARS, recent_turns
from backend.conversations import ConversationRepository
from backend.user_settings import SettingsStore, UserPreferences


@pytest.fixture
def chat_environment(tmp_path, monkeypatch):
    store = SettingsStore(tmp_path / "settings.json")
    preferences = UserPreferences.defaults()
    preferences.providers[0].selected_model = "test-local-model"
    store.save(preferences)
    repository = ConversationRepository(tmp_path / "chat.db")
    monkeypatch.setattr(main, "settings_store", store)
    monkeypatch.setattr(main, "conversation_repository", repository)
    return store, repository


def mock_model(monkeypatch, handler):
    client_type = httpx.AsyncClient
    monkeypatch.setattr(main.httpx, "AsyncClient", lambda **kwargs: client_type(
        transport=httpx.MockTransport(handler), **kwargs
    ))


def sse(content, *, reason=None, reasoning=None, space=True):
    delta = {"content": content}
    if reasoning:
        delta["reasoning_content"] = reasoning
    return "data:" + (" " if space else "") + json.dumps({
        "choices": [{"delta": delta, "finish_reason": reason}]
    }) + "\n\n"


async def events(request):
    return [json.loads(line) async for line in main._stream_model(request)]


@pytest.mark.asyncio
async def test_two_turn_chat_persists_users_and_sends_recent_context(chat_environment, monkeypatch):
    _, repository = chat_environment
    requests = []

    def model(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "Anladım."}}]})

    mock_model(monkeypatch, model)
    await main.chat(main.ChatRequest(text="Projenin adı Orion.", conversation_id="one"))
    await main.chat(main.ChatRequest(text="Adı neydi?", conversation_id="one"))
    assert requests[1]["messages"][1:] == [
        {"role": "user", "content": "Projenin adı Orion."},
        {"role": "assistant", "content": "Anladım."},
        {"role": "user", "content": "Adı neydi?"},
    ]
    assert [m["role"] for m in repository.messages("one")] == ["user", "assistant"] * 2
    assert requests[1]["model"] == "test-local-model"


@pytest.mark.asyncio
async def test_stream_filters_split_reasoning_and_accepts_no_space_sse(chat_environment, monkeypatch):
    _, repository = chat_environment
    body = "".join(sse(part, space=False) for part in ["<thi", "nk>secret", "</th", "ink>Mer", "haba"])
    body += sse("", reason="stop") + "data:[DONE]\n\n"
    mock_model(monkeypatch, lambda request: httpx.Response(200, text=body))
    result = await events(main.ChatRequest(text="Selam", conversation_id="stream"))
    assert "".join(item["text"] for item in result if item["event"] == "chunk") == "Merhaba"
    assert result[-1]["event"] == "done"
    assert [m["content"] for m in repository.messages("stream")] == ["Selam", "Merhaba"]


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [
    sse("Yarım yanıt"),
    "data:{invalid}\n\n",
    sse("", reasoning="internal only") + "data: [DONE]\n\n",
    'data: {"error": {"message": "failed"}}\n\n',
])
async def test_failed_streams_never_report_done_or_persist_assistant(chat_environment, monkeypatch, body):
    _, repository = chat_environment
    mock_model(monkeypatch, lambda request: httpx.Response(200, text=body))
    result = await events(main.ChatRequest(text="Merhaba", conversation_id="broken"))
    assert result[-1]["event"] == "error"
    assert not any(item["event"] == "done" for item in result)
    assert [m["role"] for m in repository.messages("broken")] == ["user"]


@pytest.mark.asyncio
async def test_private_chat_uses_only_ephemeral_context(chat_environment, monkeypatch):
    store, repository = chat_environment
    store.update(memory_enabled=True, memory_auto_learn=True, memory_reference_history=True)
    repository.create("Secret disk record", conversation_id="private")
    repository.add_message("private", "user", "Disk only")
    repository.add_message("private", "assistant", "Disk response")
    requests = []

    def model(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "Orion"}}]})

    mock_model(monkeypatch, model)
    await main.chat(main.ChatRequest(text="Adı?", private=True, conversation_id="private", history=[
        {"role": "user", "content": "Adı Orion"}, {"role": "assistant", "content": "Tamam"},
    ]))
    assert requests[0]["messages"][1]["content"] == "Adı Orion"
    assert "Disk only" not in json.dumps(requests)
    assert len(repository.messages("private")) == 2
    assert not main._memory_tasks


@pytest.mark.asyncio
async def test_unknown_provider_returns_actionable_stream_error(chat_environment):
    result = await events(main.ChatRequest(text="Merhaba", provider_id="missing"))
    assert result[0]["event"] == "error"
    assert "sağlayıcı" in result[0]["message"]


def test_context_is_bounded_and_omits_unanswered_prompts():
    messages = [{"role": "user", "content": "failed request"}]
    for index in range(20):
        messages.extend([{"role": "user", "content": str(index)}, {"role": "assistant", "content": "x" * 1000}])
    messages.append({"role": "user", "content": "pending"})
    selected = recent_turns(messages)
    assert selected[0]["role"] == "user"
    assert selected[-1]["role"] == "assistant"
    assert len(selected) <= 24
    assert sum(len(item["content"]) for item in selected) <= MAX_CONTEXT_CHARS
    assert all(item["content"] not in {"failed request", "pending"} for item in selected)


def test_deleting_conversation_also_removes_its_summary(chat_environment):
    _, repository = chat_environment
    repository.create("test", conversation_id="deleted")
    repository.upsert_summary("conversation", "deleted", "Must be forgotten", 2)
    repository.delete("deleted")
    assert repository.summary("conversation", "deleted") is None


@pytest.mark.asyncio
async def test_summary_updates_do_not_duplicate_user_messages(chat_environment, monkeypatch):
    import asyncio

    store, repository = chat_environment
    store.update(memory_reference_history=True)
    summaries = []

    async def summarize(**kwargs):
        summaries.append(kwargs)

    monkeypatch.setattr(main, "update_rolling_summary", summarize)
    mock_model(monkeypatch, lambda request: httpx.Response(200, json={
        "choices": [{"message": {"content": "Anladım"}}]
    }))
    await main.chat(main.ChatRequest(text="Merhaba", conversation_id="summary"))
    await asyncio.gather(*main._memory_tasks)
    assert len(summaries) == 1
    assert [m["role"] for m in repository.messages("summary")] == ["user", "assistant"]


@pytest.mark.asyncio
async def test_length_limit_reports_warning(chat_environment, monkeypatch):
    mock_model(monkeypatch, lambda request: httpx.Response(200, text=sse("Partial", reason="length")))
    result = await events(main.ChatRequest(text="Continue", private=True))
    assert [item["event"] for item in result] == ["chunk", "warning", "done"]
