import sys
from pathlib import Path

import pytest

from backend.mcp_client import MCPClient, MCPConfigStore, MCPManager, MCPServerConfig
from backend.tool_registry import ToolDefinition, ToolRegistry
from backend.tool_security import PermissionRequired, ToolExecutor, ToolSecurityStore


def test_tool_registry_namespaces_mcp_tools():
    registry = ToolRegistry()
    registry.register(ToolDefinition("local:test", "Local test", "A safe test", risk="read"))
    registry.register_mcp_tools(
        "demo",
        [{"name": "echo", "description": "Echo", "inputSchema": {"type": "object"}}],
    )

    assert registry.get("mcp:demo:echo").requires_confirmation is True
    assert len(registry.all()) == 2
    registry.remove_server("demo")
    assert registry.get("mcp:demo:echo") is None


@pytest.mark.asyncio
async def test_mcp_stdio_lifecycle_and_discovery(tmp_path):
    store = MCPConfigStore(tmp_path / "servers.json")
    server_script = Path(__file__).parent / "fixtures" / "fake_mcp_server.py"
    store.upsert(
        MCPServerConfig(
            id="fake",
            name="Fake MCP",
            command=sys.executable,
            args=["-u", str(server_script)],
        )
    )
    registry = ToolRegistry()
    manager = MCPManager(store, registry)

    tools = await manager.connect("fake")

    assert tools[0]["name"] == "echo"
    assert registry.get("mcp:fake:echo") is not None
    result = await manager.clients["fake"].call_tool("echo", {"value": "Nexus"})
    assert result["content"][0]["text"] == "Nexus"

    client = manager.clients["fake"]
    writer = client.process.stdin
    await manager.disconnect("fake")
    assert registry.all() == []
    assert writer.is_closing()
    assert client.process is None
    await client.stop()  # Repeated disconnects must be safe.


@pytest.mark.asyncio
async def test_mcp_stop_closes_stdin_after_child_has_already_exited():
    import asyncio

    client = MCPClient(MCPServerConfig("exited", "Exited child", sys.executable))
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-c", "pass", stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    client.process = process
    await process.wait()
    await client.stop()
    assert process.stdin.is_closing()
    assert client.process is None


def _fake_store(tmp_path, *server_ids):
    server_script = Path(__file__).parent / "fixtures" / "fake_mcp_server.py"
    store = MCPConfigStore(tmp_path / "servers.json")
    for server_id in server_ids:
        store.upsert(
            MCPServerConfig(
                id=server_id,
                name=f"Fake MCP {server_id}",
                command=sys.executable,
                args=["-u", str(server_script)],
            )
        )
    return store


@pytest.mark.asyncio
async def test_manager_shutdown_reaps_every_connected_server(tmp_path):
    registry = ToolRegistry()
    manager = MCPManager(_fake_store(tmp_path, "first", "second"), registry)
    await manager.connect("first")
    await manager.connect("second")
    processes = [client.process for client in manager.clients.values()]
    assert len(processes) == 2

    await manager.shutdown()

    assert manager.clients == {}
    assert registry.all() == []
    for process in processes:
        assert process.returncode is not None
    await manager.shutdown()  # A second shutdown must be harmless.


@pytest.mark.asyncio
async def test_manager_stop_is_an_alias_for_shutdown(tmp_path):
    registry = ToolRegistry()
    manager = MCPManager(_fake_store(tmp_path, "fake"), registry)
    await manager.connect("fake")
    process = manager.clients["fake"].process

    await manager.stop()

    assert manager.clients == {}
    assert registry.all() == []
    assert process.returncode is not None


def test_tool_definition_marks_legacy_authorization_fields_deprecated():
    fields = ToolDefinition.__dataclass_fields__

    for name in ("risk", "requires_confirmation"):
        assert "deprecated" in fields[name].metadata
    # Kept for backwards compatibility: authorization reads the SQLite store instead.
    assert fields["risk"].default == "sensitive"
    assert fields["requires_confirmation"].default is True


@pytest.mark.asyncio
async def test_manager_shutdown_stops_the_rest_when_one_child_is_wedged(tmp_path):
    class WedgedClient:
        process = None

        async def stop(self):
            raise RuntimeError("child is not responding")

    registry = ToolRegistry()
    manager = MCPManager(_fake_store(tmp_path, "fake"), registry)
    await manager.connect("fake")
    process = manager.clients["fake"].process
    manager.clients["wedged"] = WedgedClient()

    await manager.shutdown()

    assert process.returncode is not None
    assert manager.clients == {}
    assert registry.all() == []


@pytest.mark.asyncio
async def test_app_lifespan_reaps_connected_mcp_servers(tmp_path, monkeypatch):
    from backend import main as backend_main

    registry = ToolRegistry()
    manager = MCPManager(_fake_store(tmp_path, "fake"), registry)
    monkeypatch.setattr(backend_main, "mcp_manager", manager)
    await manager.connect("fake")
    process = manager.clients["fake"].process
    assert process.returncode is None

    assert backend_main.app.router.lifespan_context is backend_main.lifespan
    async with backend_main.lifespan(backend_main.app):
        assert process.returncode is None

    assert process.returncode is not None
    assert manager.clients == {}
    assert registry.all() == []


def _noisy_store(tmp_path, *arguments):
    script = Path(__file__).parent / "fixtures" / "noisy_mcp_server.py"
    store = MCPConfigStore(tmp_path / "servers.json")
    store.upsert(
        MCPServerConfig(
            id="noisy",
            name="Noisy MCP",
            command=sys.executable,
            args=["-u", str(script), *arguments],
        )
    )
    return store


@pytest.mark.asyncio
async def test_a_chatty_stderr_server_still_answers(tmp_path):
    registry = ToolRegistry()
    manager = MCPManager(_noisy_store(tmp_path), registry)

    tools = await manager.connect("noisy")  # Never arrives if stderr is never read.
    client = manager.clients["noisy"]
    await manager.shutdown()

    assert tools[0]["name"] == "echo"
    # The fixture writes that marker only after roughly two megabytes have gone
    # through the pipe, so seeing it means every byte was drained, not started.
    assert "NOISE_DRAIN_COMPLETE" in client.recent_stderr()
    assert client._stderr_task is None


@pytest.mark.asyncio
async def test_a_silent_server_reports_what_it_written_to_stderr(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.mcp_client.REQUEST_TIMEOUT", 0.2)
    manager = MCPManager(_noisy_store(tmp_path, "--hang"), ToolRegistry())

    with pytest.raises(TimeoutError) as failure:
        await manager.connect("noisy")

    assert "MCP_NOISE_MARKER" in str(failure.value)
    assert manager.clients == {}


@pytest.mark.asyncio
async def test_file_tool_requires_consent_and_enforces_scope(tmp_path):
    security = ToolSecurityStore(tmp_path / "security.db")
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            "local:file.read", "Read file", "Read approved text", risk="read"
        )
    )
    executor = ToolExecutor(security, registry, MCPManager(MCPConfigStore(tmp_path / "mcp.json"), registry))
    approved = tmp_path / "approved"
    approved.mkdir()
    target = approved / "note.txt"
    target.write_text("local only", encoding="utf-8")
    security.add_scope(str(approved))

    with pytest.raises(PermissionRequired):
        await executor.execute("local:file.read", {"path": str(target)})

    result = await executor.execute(
        "local:file.read", {"path": str(target)}, consent="once"
    )
    assert result["content"] == "local only"

    outside = tmp_path / "outside.txt"
    outside.write_text("blocked", encoding="utf-8")
    with pytest.raises(PermissionError):
        await executor.execute(
            "local:file.read", {"path": str(outside)}, consent="once"
        )


def test_audit_redacts_sensitive_arguments(tmp_path):
    security = ToolSecurityStore(tmp_path / "audit.db")
    security.audit("demo", "allowed", {"token": "secret", "query": "safe"})

    entry = security.audit_entries()[0]

    assert entry["arguments"] == {"token": "***", "query": "safe"}
