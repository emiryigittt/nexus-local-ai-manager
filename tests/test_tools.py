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
