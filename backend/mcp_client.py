"""Minimal MCP stdio client with explicit process lifecycle management."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from collections import deque
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from backend.app_paths import ensure_data_dirs, mcp_settings_path
from backend.tool_registry import ToolRegistry, tool_registry

PROTOCOL_VERSION = "2025-06-18"
REQUEST_TIMEOUT = 15.0
STDERR_TAIL_LINES = 40
STDERR_CHUNK_BYTES = 4096


@dataclass(slots=True)
class MCPServerConfig:
    id: str
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    enabled: bool = True


class MCPConfigStore:
    def __init__(self, path: Path | None = None):
        self.path = path or mcp_settings_path()

    def load(self) -> list[MCPServerConfig]:
        if not self.path.exists():
            return []
        try:
            values = json.loads(self.path.read_text(encoding="utf-8"))
            return [MCPServerConfig(**item) for item in values if isinstance(item, dict)]
        except (OSError, ValueError, TypeError):
            return []

    def save(self, values: list[MCPServerConfig]) -> None:
        if self.path == mcp_settings_path():
            ensure_data_dirs()
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps([asdict(item) for item in values], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def upsert(self, config: MCPServerConfig) -> None:
        values = [item for item in self.load() if item.id != config.id]
        values.append(config)
        self.save(values)


class MCPClient:
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: asyncio.subprocess.Process | None = None
        self.stderr_tail: deque[str] = deque(maxlen=STDERR_TAIL_LINES)
        self._stderr_task: asyncio.Task | None = None
        self._request_id = 0
        self._lock = asyncio.Lock()

    async def start(self) -> list[dict[str, Any]]:
        if self.process and self.process.returncode is None:
            return await self.list_tools()
        environment = os.environ.copy()
        environment["NEXUS_MCP_SERVER_ID"] = self.config.id
        self.process = await asyncio.create_subprocess_exec(
            self.config.command,
            *self.config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=environment,
        )
        self.stderr_tail.clear()
        self._stderr_task = asyncio.create_task(self._drain_stderr(self.process))
        await self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "Nexus", "version": "0.3.0-beta.3"},
            },
        )
        await self.notify("notifications/initialized", {})
        return await self.list_tools()

    async def _write(self, payload: dict[str, Any]) -> None:
        if not self.process or not self.process.stdin:
            raise RuntimeError("MCP server is not running.")
        self.process.stdin.write(
            (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode()
        )
        await self.process.stdin.drain()

    async def _drain_stderr(self, process: asyncio.subprocess.Process) -> None:
        """Read the child's stderr until it closes, keeping the last lines.

        ``start()`` asks for a stderr pipe, and an OS pipe holds only a few dozen
        kilobytes. A server that logs to stderr - most of them do - blocks in
        ``write(2)`` once that buffer is full, which then surfaces as a timeout on
        an unrelated request rather than as the harmless noise it really is.
        Reading keeps the buffer empty and keeps hold of the reason a server died.

        Chunks are read rather than lines: a chunk boundary can split a line, and
        that is only cosmetic here, whereas a line longer than the reader's limit
        would abort the drain and re-open the original deadlock.
        """
        stream = process.stderr
        if stream is None:
            return
        while True:
            try:
                chunk = await stream.read(STDERR_CHUNK_BYTES)
            except (ConnectionResetError, ValueError):
                return  # The pipe is gone; the process is on its way out anyway.
            if not chunk:
                return
            for line in chunk.decode("utf-8", errors="replace").splitlines():
                if line.strip():
                    self.stderr_tail.append(line.strip()[:500])

    def recent_stderr(self, limit: int = 3) -> str:
        """The tail of the server's stderr, newest last, for error reporting."""
        return " | ".join(list(self.stderr_tail)[-limit:])

    async def _stop_draining_stderr(self) -> None:
        """Let the reader finish now that the child is gone, without blocking."""
        task, self._stderr_task = self._stderr_task, None
        if task is None:
            return
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=0.5)
        except (TimeoutError, asyncio.CancelledError):
            task.cancel()
        except Exception:
            pass  # Losing the tail must never be what breaks a shutdown.

    async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            self._request_id += 1
            request_id = self._request_id
            await self._write(
                {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
            )
            if not self.process or not self.process.stdout:
                raise RuntimeError("MCP server is not running.")
            while True:
                try:
                    raw = await asyncio.wait_for(
                        self.process.stdout.readline(), timeout=REQUEST_TIMEOUT
                    )
                except TimeoutError as exc:
                    raise TimeoutError(
                        f"'{self.config.id}' sent nothing for {REQUEST_TIMEOUT:.0f}s. "
                        f"stderr: {self.recent_stderr() or 'empty'}"
                    ) from exc
                if not raw:
                    raise RuntimeError("MCP server closed its output stream.")
                message = json.loads(raw.decode("utf-8"))
                if message.get("id") != request_id:
                    continue
                if "error" in message:
                    raise RuntimeError(str(message["error"].get("message", "MCP error")))
                return dict(message.get("result") or {})

    async def notify(self, method: str, params: dict[str, Any]) -> None:
        await self._write({"jsonrpc": "2.0", "method": method, "params": params})

    async def list_tools(self) -> list[dict[str, Any]]:
        result = await self.request("tools/list", {})
        return list(result.get("tools") or [])

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await self.request("tools/call", {"name": name, "arguments": arguments})

    async def stop(self) -> None:
        process = self.process
        if process is None:
            return
        # Reap the stdin writer even if the child has already exited. Leaving it
        # alive lets Windows Proactor cleanup run after its event loop is gone.
        if process.stdin:
            process.stdin.close()
        if process.returncode is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
        try:
            await asyncio.wait_for(process.wait(), timeout=3.0)
        except TimeoutError:
            if process.returncode is None:
                process.kill()
            await process.wait()
        if process.stdin:
            try:
                await process.stdin.wait_closed()
            except (BrokenPipeError, ConnectionResetError):
                pass
        await self._stop_draining_stderr()
        self.process = None


class MCPManager:
    def __init__(
        self,
        store: MCPConfigStore | None = None,
        registry: ToolRegistry | None = None,
    ):
        self.store = store or MCPConfigStore()
        self.registry = registry or tool_registry
        self.clients: dict[str, MCPClient] = {}

    async def connect(self, server_id: str) -> list[dict[str, Any]]:
        config = next((item for item in self.store.load() if item.id == server_id), None)
        if config is None or not config.enabled:
            raise KeyError(server_id)
        client = MCPClient(config)
        try:
            tools = await client.start()
        except Exception:
            await client.stop()
            raise
        old = self.clients.pop(server_id, None)
        if old:
            await old.stop()
        self.clients[server_id] = client
        self.registry.register_mcp_tools(server_id, tools)
        return tools

    async def disconnect(self, server_id: str) -> None:
        client = self.clients.pop(server_id, None)
        if client:
            await client.stop()
        self.registry.remove_server(server_id)

    async def shutdown(self) -> None:
        """Stop every connected client and drop its tools from the registry.

        The application calls this once while it is shutting down, which is the only
        path that reaps children nobody disconnected explicitly. Clients are stopped
        concurrently because :meth:`MCPClient.stop` waits up to three seconds per
        child before escalating to ``kill()``; one wedged server would otherwise add
        three seconds to every exit. Failures are reported instead of raised so a
        single unresponsive child cannot keep the remaining ones running.
        """
        clients = list(self.clients.items())
        # Drop the references first: a stop that raises must not leave a client
        # behind that a later connect() would treat as still live.
        self.clients.clear()
        results = await asyncio.gather(
            *(client.stop() for _, client in clients),
            return_exceptions=True,
        )
        for (server_id, _), result in zip(clients, results, strict=True):
            if isinstance(result, BaseException):
                print(
                    f"MCP server '{server_id}' did not stop cleanly: {result!r}",
                    file=sys.stderr,
                    flush=True,
                )
            self.registry.remove_server(server_id)

    async def stop(self) -> None:
        """Alias for :meth:`shutdown` so callers can use the same verb as the clients.

        ``MCPClient`` already exposes ``stop()``; mirroring it on the manager keeps
        ``await mcp_manager.stop()`` working instead of raising ``AttributeError``.
        """
        await self.shutdown()


mcp_config_store = MCPConfigStore()
mcp_manager = MCPManager(mcp_config_store, tool_registry)
