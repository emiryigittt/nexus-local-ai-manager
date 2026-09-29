"""Minimal MCP stdio client with explicit process lifecycle management."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from backend.app_paths import ensure_data_dirs, mcp_settings_path
from backend.tool_registry import ToolRegistry, tool_registry

PROTOCOL_VERSION = "2025-06-18"


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
        await self.request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "Nexus", "version": "0.3.0-dev"},
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
                raw = await asyncio.wait_for(self.process.stdout.readline(), timeout=15.0)
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


mcp_config_store = MCPConfigStore()
mcp_manager = MCPManager(mcp_config_store, tool_registry)
