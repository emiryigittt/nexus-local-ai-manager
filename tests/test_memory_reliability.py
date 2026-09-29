import asyncio
import json

import httpx
import pytest

from backend.memory import MemoryRepository
from backend.memory_jobs import MemoryJobStatus
from backend.memory_learning import learn_from_turn, parse_candidates


def payload(content="Kısa Türkçe yanıtları tercih ederim", **kwargs):
    return json.dumps({"candidates": [{
        "content": content, "key": "response.style", "memory_type": "preference",
        "confidence": 0.9, "importance": 0.8, "sensitive": False, **kwargs,
    }]})


def mock_model(monkeypatch, handler):
    client_type = httpx.AsyncClient
    monkeypatch.setattr("backend.memory_learning.httpx.AsyncClient", lambda **kwargs: client_type(
        transport=httpx.MockTransport(handler), **kwargs,
    ))


async def extract(repository, **kwargs):
    return await learn_from_turn(
        "Kısa Türkçe cevaplar istiyorum", "Anladım", chat_url="http://localhost/chat",
        model="test", headers={}, conversation_id="synthetic", project_id=None,
        repository=repository, **kwargs,
    )


@pytest.mark.parametrize("raw", ["not json", "{}", '{"candidates":null}', '[]',
                                   payload(memory_type="unknown")])
def test_invalid_response_is_not_reported_as_no_facts(raw):
    with pytest.raises(ValueError, match="JSON"):
        parse_candidates(raw, strict=True)


def test_valid_empty_and_fenced_json_are_accepted():
    assert parse_candidates('{"candidates":[]}', strict=True) == []
    assert len(parse_candidates("```json\n" + payload() + "\n```", strict=True)) == 1


async def test_schema_fallback_persists_reviewable_candidate(monkeypatch, tmp_path):
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        if len(requests) == 1:
            return httpx.Response(400, text="response_format json_schema unsupported")
        return httpx.Response(200, json={"choices": [{"message": {"content": payload()}}]})

    mock_model(monkeypatch, handler)
    repository = MemoryRepository(tmp_path / "memory.db")
    assert await extract(repository) == 1
    assert "response_format" in requests[0]
    assert "response_format" not in requests[1]
    reopened = MemoryRepository(repository.path)
    assert not reopened.for_context()
    candidate = reopened.list()[0]
    assert candidate["status"] == "candidate"
    assert reopened.activate(candidate["id"])
    assert len(MemoryRepository(repository.path).for_context()) == 1


@pytest.mark.parametrize("status,message,attempts", [(401, "unauthorized", 1),
    (400, "model missing", 1), (422, "response_format unsupported", 2)])
async def test_retries_only_schema_errors_once(monkeypatch, tmp_path, status, message, attempts):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status, text=message)

    mock_model(monkeypatch, handler)
    repository = MemoryRepository(tmp_path / "memory.db")
    with pytest.raises(httpx.HTTPStatusError):
        await extract(repository)
    assert len(calls) == attempts
    assert repository.list() == []


@pytest.mark.parametrize("content,allowed", [
    ("Kısa yanıtları tercih ederim", False), ("API key: sk-abcdefghijklmnop", True),
])
async def test_consent_revocation_and_sensitive_text_prevent_save(monkeypatch, tmp_path, content, allowed):
    mock_model(monkeypatch, lambda request: httpx.Response(200, json={
        "choices": [{"message": {"content": payload(content)}}],
    }))
    repository = MemoryRepository(tmp_path / "memory.db")
    assert await extract(repository, should_save=lambda: allowed) == 0
    assert not repository.list()


def test_status_is_durable_and_old_job_cannot_replace_new(tmp_path):
    path = tmp_path / "memory.db"
    status = MemoryJobStatus(path)
    assert status.latest() is None
    assert not path.exists()
    old, new = status.start(), status.start()
    status.finish(old, "failed")
    assert status.latest()["state"] == "running"
    status.finish(new, "completed", 2)
    assert MemoryJobStatus(path).latest()["count"] == 2
    assert set(status.latest()) == {"state", "count", "updated"}


@pytest.mark.parametrize("error,state", [(httpx.ConnectError("secret"), "model_unavailable"),
    (httpx.ReadTimeout("secret"), "timeout"), (ValueError("secret"), "invalid_output"),
    (RuntimeError("secret"), "failed")])
async def test_background_failure_has_content_free_visible_status(monkeypatch, tmp_path, error, state):
    from backend import main
    from backend.user_settings import UserPreferences

    preferences = UserPreferences.defaults()
    preferences.memory_auto_learn = True
    monkeypatch.setattr(main.settings_store, "load", lambda: preferences)
    monkeypatch.setattr(main, "_model_connection", lambda data: ("url", "model", {}))
    status = MemoryJobStatus(tmp_path / "status.db")
    monkeypatch.setattr(main, "memory_job_status", status)

    async def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(main, "learn_from_turn", fail)
    main._schedule_memory_learning(main.ChatRequest(text="Synthetic"), "Response")
    await asyncio.gather(*main._memory_tasks)
    assert status.latest()["state"] == state
    assert "secret" not in str(status.latest())


async def test_private_and_disabled_learning_create_no_status(monkeypatch, tmp_path):
    from backend import main
    from backend.user_settings import UserPreferences

    preferences = UserPreferences.defaults()
    status = MemoryJobStatus(tmp_path / "status.db")
    monkeypatch.setattr(main.settings_store, "load", lambda: preferences)
    monkeypatch.setattr(main, "memory_job_status", status)
    main._schedule_memory_learning(main.ChatRequest(text="Synthetic"), "Response")
    preferences.memory_auto_learn = True
    main._schedule_memory_learning(main.ChatRequest(text="Synthetic", private=True), "Response")
    assert status.latest() is None
