"""Central metadata registry for built-in and MCP-provided tools."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    id: str
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=lambda: {"type": "object"})
    source: str = "built-in"
    server_id: str = ""
    risk: str = "sensitive"
    requires_confirmation: bool = True

    def public(self) -> dict[str, Any]:
        return asdict(self)


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if not tool.id or not tool.name:
            raise ValueError("Tool id and name are required.")
        if tool.risk not in {"read", "write", "network", "sensitive"}:
            raise ValueError("Unknown tool risk level.")
        self._tools[tool.id] = tool

    def register_mcp_tools(self, server_id: str, values: list[dict[str, Any]]) -> None:
        self.remove_server(server_id)
        for value in values:
            raw_name = str(value.get("name", "")).strip()
            if not raw_name:
                continue
            self.register(
                ToolDefinition(
                    id=f"mcp:{server_id}:{raw_name}",
                    name=raw_name,
                    description=str(value.get("description", "")).strip(),
                    input_schema=dict(value.get("inputSchema") or {"type": "object"}),
                    source="mcp",
                    server_id=server_id,
                    risk="sensitive",
                    requires_confirmation=True,
                )
            )

    def remove_server(self, server_id: str) -> None:
        self._tools = {
            key: value for key, value in self._tools.items() if value.server_id != server_id
        }

    def get(self, tool_id: str) -> ToolDefinition | None:
        return self._tools.get(tool_id)

    def all(self) -> list[ToolDefinition]:
        return sorted(self._tools.values(), key=lambda item: (item.source, item.name.casefold()))


tool_registry = ToolRegistry()
