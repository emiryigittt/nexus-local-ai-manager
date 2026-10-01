"""FastAPI gateway between the Nexus desktop UI and an OpenAI-compatible API."""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator
from dataclasses import asdict
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import StreamingResponse

from backend.actions import action_registry
from backend.chat_context import recent_turns
from backend.config import settings
from backend.conversation_summaries import update_rolling_summary
from backend.conversations import conversation_repository
from backend.documents import document_repository
from backend.embeddings import embed_texts
from backend.identity import identity_instruction, profile_context, profile_memories
from backend.mcp_client import MCPServerConfig, mcp_config_store, mcp_manager
from backend.memory import memory_repository
from backend.memory_jobs import memory_job_status
from backend.memory_learning import learn_from_turn
from backend.memory_retrieval import retrieve_memories
from backend.model_output import VisibleAnswer
from backend.providers import discover_providers, probe_provider, select_provider
from backend.search_engine import conduct_deep_research
from backend.tool_registry import tool_registry
from backend.tool_security import (
    PermissionRequired,
    tool_executor,
    tool_security_store,
)
from backend.user_settings import ProviderProfile, settings_store

app = FastAPI(
    title="Nexus Local API",
    description="Local gateway for the Nexus desktop command center.",
    version="0.3.0-beta.1",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://{settings.backend_host}:{settings.backend_port}",
        f"http://localhost:{settings.backend_port}",
    ],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


class ContextMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=50_000)


class ChatRequest(BaseModel):
    text: str = Field(default="", max_length=50_000)
    image: str | None = Field(default=None, max_length=20_000_000)
    conversation_id: str | None = Field(default=None, max_length=64)
    provider_id: str | None = Field(default=None, max_length=100)
    model_id: str | None = Field(default=None, max_length=300)
    private: bool = False
    action_id: str | None = Field(default=None, max_length=100)
    use_knowledge: bool = False
    project_id: str | None = Field(default=None, max_length=100)
    # Private sessions keep their context in the client, never in SQLite.
    history: list[ContextMessage] = Field(default_factory=list, max_length=24)


class ChatResponse(BaseModel):
    response: str
    memory_sources: list[dict[str, Any]] = Field(default_factory=list)


class ProviderSelection(BaseModel):
    provider_id: str = Field(min_length=1, max_length=100)
    model_id: str = Field(default="", max_length=300)


class PreferencesUpdate(BaseModel):
    language: str | None = Field(default=None, pattern="^(tr|en)$")
    theme: str | None = Field(default=None, pattern="^(dark|light|system)$")
    global_shortcut: str | None = Field(default=None, max_length=50)
    setup_complete: bool | None = None
    tts_enabled: bool | None = None
    tts_backend: str | None = Field(default=None, max_length=30)
    tts_local_voice: int | None = Field(default=None, ge=0, le=9)
    tts_edge_voice: str | None = Field(default=None, pattern="^(tr-TR-AhmetNeural|tr-TR-EmelNeural|en-US-AriaNeural|en-US-GuyNeural)$")
    tts_speed: float | None = Field(default=None, ge=0.8, le=1.3)
    tts_steps: int | None = Field(default=None, ge=4, le=8)
    voice_input_device: str | None = Field(default=None, max_length=1000)
    voice_output_device: str | None = Field(default=None, max_length=1000)
    voice_input_mode: str | None = Field(default=None, pattern="^(toggle|push_to_talk|vad)$")
    voice_auto_finish: bool | None = None
    voice_review_before_send: bool | None = None
    voice_transcription_model: str | None = Field(default=None, pattern="^(base|small)$")
    voice_silence_seconds: float | None = Field(default=None, ge=0.3, le=3.0)
    voice_threshold: float | None = Field(default=None, ge=0.001, le=0.2)
    wake_word_enabled: bool | None = None
    wake_word_on_startup: bool | None = None
    wake_word_threshold: float | None = Field(default=None, ge=0.001, le=0.2)
    cloud_speech_consent: bool | None = None
    web_consent: bool | None = None
    memory_enabled: bool | None = None
    personal_questions_enabled: bool | None = None
    memory_auto_learn: bool | None = None
    memory_reference_history: bool | None = None
    clipboard_policy: str | None = Field(default=None, pattern="^(ask|always|never)$")


class ConversationUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=80)
    pinned: bool | None = None


class DocumentImport(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    content: str = Field(min_length=1, max_length=5_000_000)
    source_type: str = Field(default="text", max_length=30)


class MemoryCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    memory_type: str = Field(
        default="fact",
        pattern="^(preference|fact|goal|instruction|project_decision)$",
    )
    scope: str = Field(default="global", pattern="^(global|project)$")
    project_id: str | None = Field(default=None, max_length=100)
    source_conversation_id: str | None = Field(default=None, max_length=64)
    source_message_id: str | None = Field(default=None, max_length=64)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    expires_at: str | None = Field(default=None, max_length=40)
    pinned: bool = False
    status: str = Field(
        default="active", pattern="^(candidate|active|superseded|disabled)$"
    )
    supersedes_id: str | None = Field(default=None, max_length=64)
    memory_key: str | None = Field(
        default=None, max_length=120, pattern=r"^[A-Za-z0-9_.-]+$"
    )


class MemoryUpdate(MemoryCreate):
    enabled: bool = True


class MCPServerCreate(BaseModel):
    id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=120)
    command: str = Field(min_length=1, max_length=1000)
    args: list[str] = Field(default_factory=list, max_length=50)
    enabled: bool = True


class ToolCall(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)
    consent: str | None = Field(default=None, pattern="^(once|always|deny)$")


class FilesystemScope(BaseModel):
    path: str = Field(min_length=1, max_length=2000)


def _provider_for(data: ChatRequest) -> ProviderProfile:
    preferences = settings_store.load()
    wanted = data.provider_id or preferences.selected_provider_id
    profile = next((item for item in preferences.providers if item.id == wanted), None)
    if profile is None:
        raise HTTPException(status_code=422, detail="Seçili sağlayıcı bulunamadı. Ayarlardan sağlayıcı seçin.")
    if not profile.enabled:
        raise HTTPException(status_code=422, detail="Seçili sağlayıcı devre dışı.")
    return profile


def _model_connection(data: ChatRequest) -> tuple[str, str, dict[str, str]]:
    profile = _provider_for(data)
    uses_environment = profile.base_url.rstrip("/") == settings.api_base_url.rstrip("/")
    model = data.model_id or profile.selected_model or (settings.model if uses_environment else "")
    if not model:
        raise HTTPException(status_code=422, detail="Ayarlardan bu sağlayıcı için bir model seçin.")
    headers = settings.provider_headers if uses_environment else {}
    return f"{profile.base_url.rstrip('/')}/chat/completions", model, headers


def _record_user_message(data: ChatRequest) -> None:
    if data.private or not data.conversation_id:
        return
    profile = _provider_for(data)
    conversation_repository.create(
        data.text or "Görsel analizi",
        provider_id=profile.id,
        model_id=data.model_id or profile.selected_model or settings.model,
        conversation_id=data.conversation_id,
    )
    conversation_repository.add_message(
        data.conversation_id,
        "user",
        data.text or "[Görsel]",
        metadata={"has_image": bool(data.image)},
    )


_memory_tasks: set[asyncio.Task[Any]] = set()


async def _prioritize_interactive_request():
    """Stop optional model work before submitting the next interactive answer."""
    pending = [task for task in _memory_tasks if not task.done()]
    for task in pending:
        task.cancel()
    if pending:
        # A provider must not turn cancelled optional work into another long wait.
        await asyncio.wait(pending, timeout=0.2)


def _schedule_memory_learning(data: ChatRequest, assistant_text: str) -> None:
    preferences = settings_store.load()
    if data.private or not preferences.memory_auto_learn or not data.text.strip():
        return
    chat_url, model, headers = _model_connection(data)
    job_id = memory_job_status.start()

    async def learn():
        try:
            await asyncio.sleep(1.0)
            count = await learn_from_turn(
                data.text,
                assistant_text,
                chat_url=chat_url,
                model=model,
                headers=headers,
                conversation_id=data.conversation_id,
                project_id=data.project_id,
                should_save=lambda: settings_store.load().memory_auto_learn,
            )
            memory_job_status.finish(job_id, "completed" if settings_store.load().memory_auto_learn else "cancelled", count)
        except asyncio.CancelledError:
            memory_job_status.finish(job_id, "cancelled")
            raise
        except httpx.ConnectError:
            memory_job_status.finish(job_id, "model_unavailable")
        except httpx.TimeoutException:
            memory_job_status.finish(job_id, "timeout")
        except ValueError:
            memory_job_status.finish(job_id, "invalid_output")
        except Exception:
            # No prompts, generated facts, server payloads, or secrets in status storage.
            memory_job_status.finish(job_id, "failed")

    task = asyncio.create_task(learn())
    _memory_tasks.add(task)

    def completed(done: asyncio.Task[Any]) -> None:
        _memory_tasks.discard(done)
        if done.cancelled():
            memory_job_status.finish(job_id, "cancelled")
        try:
            done.exception()
        except (asyncio.CancelledError, Exception):
            pass

    task.add_done_callback(completed)


def _schedule_summary_updates(data: ChatRequest, assistant_text: str) -> None:
    preferences = settings_store.load()
    if data.private or not preferences.memory_reference_history or not data.text.strip():
        return
    chat_url, model, headers = _model_connection(data)
    targets: list[tuple[str, str]] = []
    if data.conversation_id:
        targets.append(("conversation", data.conversation_id))
    if data.project_id:
        targets.append(("project", data.project_id))
    for kind, scope_id in targets:
        async def summarize(kind=kind, scope_id=scope_id):
            await asyncio.sleep(1.0)
            await update_rolling_summary(
                kind=kind, scope_id=scope_id, user_text=data.text,
                assistant_text=assistant_text, chat_url=chat_url, model=model, headers=headers,
            )

        task = asyncio.create_task(
            summarize()
        )
        _memory_tasks.add(task)

        def completed(done: asyncio.Task[Any]) -> None:
            _memory_tasks.discard(done)
            try:
                done.exception()
            except (asyncio.CancelledError, Exception):
                pass

        task.add_done_callback(completed)


def _clean_model_output(result: dict[str, Any]) -> str:
    if not isinstance(result, dict):
        raise HTTPException(status_code=502, detail="Model yanıtı beklenen biçimde değil.")
    choices = result.get("choices") or []
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise HTTPException(status_code=502, detail="The AI provider returned no choices.")

    message = choices[0].get("message") or {}
    if not isinstance(message, dict):
        raise HTTPException(status_code=502, detail="Model mesajı beklenen biçimde değil.")
    content = message.get("content") or ""
    if not isinstance(content, str):
        raise HTTPException(status_code=502, detail="Model yanıtı geçerli metin içermiyor.")
    content = VisibleAnswer().feed(content, final=True).strip()
    if not content:
        raise HTTPException(status_code=502, detail="The model returned an empty response.")
    return content


async def _build_prompt(
    data: ChatRequest, *, include_metadata: bool = False, allow_personal_question: bool = True
) -> tuple[Any, str] | tuple[Any, str, list[dict[str, Any]]]:
    memory_sources: list[dict[str, Any]] = []
    preferences = settings_store.load()
    profile = profile_memories(memory_repository, preferences, private=data.private)
    summary = memory_repository.profile_summary() if preferences.memory_enabled and not data.private else ""
    personal_context = profile_context(profile, summary)
    memory_sources.extend(
        {"id": item["id"], "content": item["content"], "memory_type": item["memory_type"],
         "source_conversation_id": item.get("source_conversation_id"), "score": None}
        for item in profile
    )

    def result(content: Any, instruction: str, mode: str = "chat"):
        if personal_context:
            if isinstance(content, list):
                content[0] = {"type": "text", "text": personal_context + "\n\nCurrent request:\n" + content[0]["text"]}
            else:
                content = personal_context + "\n\nCurrent request:\n" + content
        provider = _provider_for(data)
        model = data.model_id or provider.selected_model
        if not model and provider.base_url.rstrip("/") == settings.api_base_url.rstrip("/"):
            model = settings.model
        instruction = identity_instruction(
            preferences, provider, private=data.private, mode=mode,
            model=model, allow_question=allow_personal_question,
        ) + "\n" + instruction
        if include_metadata:
            return content, instruction, memory_sources
        return content, instruction

    text = data.text.strip()
    if data.action_id:
        action = action_registry.get(data.action_id)
        if action is None:
            raise HTTPException(status_code=404, detail="Action not found.")
        if not text:
            raise HTTPException(status_code=422, detail="The action requires input.")
        text = action.render(text)
    if data.image:
        prompt = text or "Bu görseli incele ve önemli detayları açıkla."
        return result(
            [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{data.image}"},
                },
            ],
            "For this multimodal request, describe the attached image carefully, distinguishing observations from guesses.",
            "vision",
        )

    search_match = re.match(r"^/(?:web|ara|search)\s+(.+)$", text, re.DOTALL)
    if search_match:
        if not settings_store.load().web_consent:
            raise HTTPException(
                status_code=403,
                detail="Web araştırması ağ erişimi gerektiriyor. Ayarlardan web iznini etkinleştirin.",
            )
        query = search_match.group(1).strip()
        research = await conduct_deep_research(query, max_sites=10, top_filtered=4)
        if research.get("error"):
            raise HTTPException(status_code=502, detail=research["error"])
        return result(
            f"Research question: {query}\n\nSources:\n{research['brief']}\n\n"
            "Synthesize a useful answer. Cite claims with [1], [2], etc. "
            "End with a Sources section containing the supplied URLs.",
            "Use the supplied sources accurately and be transparent about uncertainty.",
            "research",
        )

    if not text:
        raise HTTPException(status_code=422, detail="Enter a prompt or attach an image.")
    if data.use_knowledge:
        query_vector: list[float] | None = None
        embedding_model = ""
        try:
            async with asyncio.timeout(0.6):
                vectors, embedding_model = ([], "") if data.private else await embed_texts([text])
            query_vector = vectors[0] if vectors else None
        except (TimeoutError, httpx.HTTPError, ValueError):
            pass
        sources = document_repository.search(
            text, query_vector=query_vector, embedding_model=embedding_model
        )
        if sources:
            context = "\n\n".join(
                f"[{index}] {item['name']} · bölüm {item['position'] + 1}\n{item['content']}"
                for index, item in enumerate(sources, 1)
            )
            text = (
                f"Kullanıcı sorusu: {text}\n\nYerel kaynaklar:\n{context}\n\n"
                "Yalnızca desteklenen iddialarda [1], [2] biçiminde kaynak göster."
            )
    if preferences.memory_reference_history and not data.private:
        summary_parts: list[str] = []
        if data.conversation_id:
            summary = conversation_repository.summary("conversation", data.conversation_id)
            if summary:
                summary_parts.append(f"Konuşma özeti:\n{summary['summary']}")
        if data.project_id:
            summary = conversation_repository.summary("project", data.project_id)
            if summary:
                summary_parts.append(f"Proje özeti:\n{summary['summary']}")
        if summary_parts:
            text = "\n\n".join(summary_parts) + f"\n\nGüncel istek:\n{text}"
    if preferences.memory_enabled and not data.private:
        memories = await retrieve_memories(data.text, data.project_id)
        memories = [item for item in memories if item["id"] not in {record["id"] for record in profile}]
        if memories:
            memory_sources.extend(
                {
                    "id": item["id"],
                    "content": item["content"],
                    "memory_type": item["memory_type"],
                    "source_conversation_id": item.get("source_conversation_id"),
                    "score": item.get("retrieval_score"),
                }
                for item in memories
            )
            facts = "\n".join(f"- {item['content']}" for item in memories)
            text = f"Kullanıcının açıkça kaydettiği bilgiler:\n{facts}\n\n{text}"
    return result(
        text,
        "Give useful, clear answers in the language used by the user.",
        "action" if data.action_id else "chat",
    )


async def _model_payload(
    data: ChatRequest, *, stream: bool = False
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    _, model, _ = _model_connection(data)
    history = []
    if data.private:
        history = recent_turns(item.model_dump() for item in data.history)
    elif data.conversation_id:
        history = recent_turns(conversation_repository.messages(data.conversation_id))
    recent_answers = [item["content"] for item in history if item["role"] == "assistant"][-2:]
    user_content, system_instruction, memory_sources = await _build_prompt(
        data, include_metadata=True,
        allow_personal_question=not any("?" in answer for answer in recent_answers),
    )
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system_instruction},
            *history,
            {"role": "user", "content": user_content},
        ],
        "max_tokens": settings.max_tokens,
        "temperature": settings.temperature,
        "stream": stream,
    }, memory_sources


def _stream_event(event: str, **payload: Any) -> str:
    return json.dumps({"event": event, **payload}, ensure_ascii=False) + "\n"


async def _stream_model(data: ChatRequest) -> AsyncIterator[str]:
    """Translate the provider's SSE stream into compact newline-delimited JSON."""
    try:
        await _prioritize_interactive_request()
        payload, memory_sources = await _model_payload(data, stream=True)
        chat_url, _, headers = _model_connection(data)
        _record_user_message(data)
        response_parts: list[str] = []
        answer = VisibleAnswer()
        completed = False
        finish_reason = None
        if memory_sources:
            yield _stream_event("memory_sources", sources=memory_sources)
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            async with client.stream(
                "POST",
                chat_url,
                json=payload,
                headers=headers,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    encoded = line[5:].strip()
                    if encoded == "[DONE]":
                        completed = True
                        break
                    try:
                        chunk = json.loads(encoded)
                    except ValueError as exc:
                        raise ValueError("Model geçersiz bir yanıt akışı gönderdi. Yeniden deneyin.") from exc
                    if not isinstance(chunk, dict):
                        raise ValueError("Model yanıt akışı beklenen biçimde değil.")
                    if chunk.get("error"):
                        raise ValueError("Model üretim sırasında hata bildirdi. Model sunucusunu kontrol edin.")
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    finish_reason = choices[0].get("finish_reason") or finish_reason
                    if finish_reason:
                        completed = True
                    if delta.get("tool_calls") or finish_reason == "tool_calls":
                        raise ValueError("Model araç çağrısı üretti; bu sohbet yolu henüz araç çağrılarını çalıştırmıyor.")
                    text = delta.get("content") or ""
                    if not isinstance(text, str):
                        raise ValueError("Model yanıtı geçerli metin içermiyor.")
                    text = answer.feed(text)
                    if text:
                        response_parts.append(text)
                        yield _stream_event("chunk", text=text)
        if not completed:
            raise ValueError("Model bağlantısı yanıt tamamlanmadan kesildi. Yeniden deneyin.")
        tail = answer.feed("", final=True)
        if tail:
            response_parts.append(tail)
            yield _stream_event("chunk", text=tail)
        if not "".join(response_parts).strip():
            raise ValueError("Model kullanılabilir bir yanıt üretmedi. Modeli ve yanıt uzunluğu ayarını kontrol edin.")
        if data.conversation_id and not data.private and response_parts:
            conversation_repository.add_message(
                data.conversation_id, "assistant", "".join(response_parts)
            )
        if response_parts:
            _schedule_memory_learning(data, "".join(response_parts))
            _schedule_summary_updates(data, "".join(response_parts))
        if finish_reason == "length":
            yield _stream_event("warning", message="Yanıt uzunluk sınırına ulaştı. Devam etmesini isteyebilirsiniz.")
        yield _stream_event("done", finish_reason=finish_reason)
    except HTTPException as exc:
        yield _stream_event("error", message=str(exc.detail))
    except httpx.ConnectError:
        yield _stream_event(
            "error",
            message=f"Seçili model sunucusuna ulaşılamıyor: {_provider_for(data).base_url}",
        )
    except httpx.TimeoutException:
        yield _stream_event("error", message="The model response timed out.")
    except httpx.HTTPStatusError as exc:
        yield _stream_event(
            "error",
            message=f"AI provider error: {exc.response.text[:500] or exc}",
        )
    except Exception as exc:
        yield _stream_event("error", message=str(exc))


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "Nexus Local API", "status": "running", "docs": "/docs"}


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Return gateway status without requiring the model server."""
    return {"healthy": True, "model": settings.model, "provider": settings.api_base_url}


@app.get("/api/v1/settings")
async def get_preferences() -> dict[str, Any]:
    """Return durable non-secret preferences."""
    return asdict(settings_store.load())


@app.get("/api/v1/actions")
async def list_actions() -> list[dict[str, str]]:
    return [item.public() for item in action_registry.all()]


@app.get("/api/v1/tools")
async def list_tools() -> list[dict[str, Any]]:
    return [item.public() for item in tool_registry.all()]


@app.post("/api/v1/tools/{tool_id}/call")
async def call_tool(tool_id: str, data: ToolCall) -> dict[str, Any]:
    try:
        return await tool_executor.execute(tool_id, data.arguments, data.consent)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Tool not found.") from exc
    except PermissionRequired as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/v1/tools/audit")
async def list_tool_audit(limit: int = Query(default=100, ge=1, le=500)) -> list[dict[str, Any]]:
    return tool_security_store.audit_entries(limit)


@app.get("/api/v1/tools/filesystem-scopes")
async def list_filesystem_scopes() -> list[str]:
    return tool_security_store.scopes()


@app.post("/api/v1/tools/filesystem-scopes", status_code=201)
async def add_filesystem_scope(data: FilesystemScope) -> dict[str, str]:
    path = Path(data.path).expanduser()
    if not path.is_dir():
        raise HTTPException(status_code=422, detail="Scope must be an existing directory.")
    return {"path": tool_security_store.add_scope(str(path))}


@app.get("/api/v1/mcp/servers")
async def list_mcp_servers() -> list[dict[str, Any]]:
    return [
        asdict(item) | {"connected": item.id in mcp_manager.clients}
        for item in mcp_config_store.load()
    ]


@app.post("/api/v1/mcp/servers", status_code=201)
async def save_mcp_server(data: MCPServerCreate) -> dict[str, Any]:
    config = MCPServerConfig(**data.model_dump())
    mcp_config_store.upsert(config)
    return asdict(config)


@app.post("/api/v1/mcp/servers/{server_id}/connect")
async def connect_mcp_server(server_id: str) -> dict[str, Any]:
    try:
        tools = await mcp_manager.connect(server_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="MCP server not found or disabled.") from exc
    except (OSError, RuntimeError, ValueError, TimeoutError) as exc:
        raise HTTPException(status_code=502, detail=f"MCP connection failed: {exc}") from exc
    return {"connected": True, "tools": tools}


@app.delete("/api/v1/mcp/servers/{server_id}/connection", status_code=204)
async def disconnect_mcp_server(server_id: str) -> Response:
    await mcp_manager.disconnect(server_id)
    return Response(status_code=204)


@app.get("/api/v1/documents")
async def list_documents() -> list[dict[str, Any]]:
    return document_repository.list()


@app.post("/api/v1/documents", status_code=201)
async def import_document(data: DocumentImport) -> dict[str, str]:
    try:
        identifier = document_repository.add(data.name, data.content, data.source_type)
        chunks = document_repository.chunk_records(identifier)
        vectors: list[list[float]] = []
        model = ""
        for start in range(0, len(chunks), 32):
            batch_vectors, model = await embed_texts(
                [item["content"] for item in chunks[start : start + 32]]
            )
            if not batch_vectors:
                vectors = []
                break
            vectors.extend(batch_vectors)
        if vectors:
            document_repository.set_embeddings(identifier, vectors, model)
    except (ValueError, httpx.HTTPError) as exc:
        if "identifier" in locals():
            document_repository.delete(identifier)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"id": identifier}


@app.get("/api/v1/documents/search")
async def search_documents(
    query: str = Query(min_length=1, max_length=1000),
) -> list[dict[str, Any]]:
    return document_repository.search(query)


@app.delete("/api/v1/documents/{document_id}", status_code=204)
async def delete_document(document_id: str) -> Response:
    if not document_repository.delete(document_id):
        raise HTTPException(status_code=404, detail="Document not found.")
    return Response(status_code=204)


@app.get("/api/v1/memories")
async def list_memories() -> list[dict[str, Any]]:
    return memory_repository.list()


@app.post("/api/v1/memories", status_code=201)
async def create_memory(data: MemoryCreate) -> dict[str, str]:
    try:
        identifier = memory_repository.add(
            data.content,
            data.memory_type,
            data.scope,
            data.project_id,
            data.source_conversation_id,
            data.source_message_id,
            data.confidence,
            data.importance,
            data.expires_at,
            data.pinned,
            data.status,
            data.supersedes_id,
            data.memory_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"id": identifier}


@app.put("/api/v1/memories/{memory_id}")
async def update_memory(memory_id: str, data: MemoryUpdate) -> dict[str, bool]:
    if not memory_repository.update(
        memory_id,
        data.content,
        data.enabled,
        data.memory_type,
        data.scope,
        data.project_id,
        data.status,
        data.confidence,
        data.importance,
        data.pinned,
        data.expires_at,
    ):
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"updated": True}


@app.get("/api/v1/memories/{memory_id}/versions")
async def list_memory_versions(memory_id: str) -> list[dict[str, Any]]:
    return memory_repository.versions(memory_id)


@app.post("/api/v1/memories/{memory_id}/activate")
async def activate_memory(memory_id: str) -> dict[str, bool]:
    if not memory_repository.activate(memory_id):
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"activated": True}


@app.delete("/api/v1/memories/{memory_id}", status_code=204)
async def delete_memory(memory_id: str) -> Response:
    if not memory_repository.delete(memory_id):
        raise HTTPException(status_code=404, detail="Memory not found.")
    return Response(status_code=204)


@app.put("/api/v1/settings")
async def update_preferences(data: PreferencesUpdate) -> dict[str, Any]:
    changes = data.model_dump(exclude_none=True)
    return asdict(settings_store.update(**changes))


@app.get("/api/v1/providers")
async def list_providers() -> list[dict[str, Any]]:
    return [asdict(item) for item in settings_store.load().providers]


@app.post("/api/v1/providers/discover")
async def discover_local_providers() -> list[dict[str, Any]]:
    return await discover_providers()


@app.post("/api/v1/providers/select")
async def choose_provider(data: ProviderSelection) -> dict[str, Any]:
    try:
        profile = select_provider(data.provider_id, data.model_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Provider not found.") from exc
    return asdict(profile)


@app.get("/api/v1/providers/{provider_id}/probe")
async def check_provider(provider_id: str) -> dict[str, Any]:
    profile = next(
        (item for item in settings_store.load().providers if item.id == provider_id), None
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Provider not found.")
    return await probe_provider(profile, timeout=5.0)


@app.get("/api/v1/conversations")
async def list_conversations(
    query: str = Query(default="", max_length=200), limit: int = Query(default=100, ge=1, le=500)
) -> list[dict[str, Any]]:
    return conversation_repository.list(query, limit)


@app.get("/api/v1/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> dict[str, Any]:
    rows = [item for item in conversation_repository.list(limit=500) if item["id"] == conversation_id]
    if not rows:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"conversation": rows[0], "messages": conversation_repository.messages(conversation_id)}


@app.patch("/api/v1/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, data: ConversationUpdate) -> dict[str, bool]:
    changed = conversation_repository.update(
        conversation_id, title=data.title, pinned=data.pinned
    )
    if not changed:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"updated": True}


@app.delete("/api/v1/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: str) -> Response:
    if not conversation_repository.delete(conversation_id):
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return Response(status_code=204)


@app.get("/health/provider")
async def provider_health() -> dict[str, Any]:
    """Verify that the configured OpenAI-compatible provider is reachable."""
    profile = _provider_for(ChatRequest())
    result = await probe_provider(profile, timeout=5.0)
    if not result["healthy"]:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot reach the AI provider at {profile.base_url}: {result['error']}",
        )
    return result


@app.post("/chat", response_model=ChatResponse)
async def chat(data: ChatRequest) -> ChatResponse:
    await _prioritize_interactive_request()
    payload, memory_sources = await _model_payload(data)
    chat_url, _, headers = _model_connection(data)
    _record_user_message(data)

    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            response = await client.post(
                chat_url, json=payload, headers=headers
            )
            response.raise_for_status()
            result = response.json()
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"AI provider is offline at {_provider_for(data).base_url}. "
                "Start LM Studio (or configure NEXUS_API_BASE_URL)."
            ),
        ) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="The model response timed out.") from exc
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500] or str(exc)
        raise HTTPException(status_code=502, detail=f"AI provider error: {detail}") from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="AI provider returned invalid JSON.") from exc

    content = _clean_model_output(result)
    if data.conversation_id and not data.private:
        conversation_repository.add_message(data.conversation_id, "assistant", content)
    _schedule_memory_learning(data, content)
    _schedule_summary_updates(data, content)
    return ChatResponse(response=content, memory_sources=memory_sources)


@app.post("/chat/stream")
async def chat_stream(data: ChatRequest) -> StreamingResponse:
    """Stream model tokens so the UI and local voice can respond immediately."""
    return StreamingResponse(
        _stream_model(data),
        media_type="application/x-ndjson; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
