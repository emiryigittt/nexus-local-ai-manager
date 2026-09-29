"""Consent, filesystem scoping, execution, and auditing for Nexus tools."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app_paths import database_path, ensure_data_dirs
from backend.mcp_client import MCPManager, mcp_manager
from backend.tool_registry import ToolDefinition, ToolRegistry, tool_registry

SENSITIVE_KEYS = {"api_key", "authorization", "password", "secret", "token"}


class PermissionRequired(RuntimeError):
    pass


class ToolSecurityStore:
    def __init__(self, path: Path | None = None):
        self.path = path or database_path()
        if path is None:
            ensure_data_dirs()
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS tool_permissions (
                    tool_id TEXT PRIMARY KEY, decision TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS filesystem_scopes (
                    path TEXT PRIMARY KEY, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tool_audit (
                    id TEXT PRIMARY KEY, tool_id TEXT NOT NULL, status TEXT NOT NULL,
                    arguments TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def permission(self, tool_id: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT decision FROM tool_permissions WHERE tool_id = ?", (tool_id,)
            ).fetchone()
        return str(row["decision"]) if row else None

    def set_permission(self, tool_id: str, decision: str) -> None:
        if decision not in {"allow", "deny"}:
            raise ValueError("Persistent decision must be allow or deny.")
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO tool_permissions(tool_id, decision, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(tool_id) DO UPDATE SET decision=excluded.decision,
                updated_at=excluded.updated_at""",
                (tool_id, decision, datetime.now(UTC).isoformat()),
            )

    def add_scope(self, path: str) -> str:
        resolved = str(Path(path).expanduser().resolve())
        with self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO filesystem_scopes(path, created_at) VALUES (?, ?)",
                (resolved, datetime.now(UTC).isoformat()),
            )
        return resolved

    def scopes(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute("SELECT path FROM filesystem_scopes ORDER BY path").fetchall()
        return [str(row["path"]) for row in rows]

    @staticmethod
    def redact(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: "***" if key.casefold() in SENSITIVE_KEYS else ToolSecurityStore.redact(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [ToolSecurityStore.redact(item) for item in value]
        return value

    def audit(self, tool_id: str, status: str, arguments: dict[str, Any], detail: str = "") -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO tool_audit VALUES (?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    tool_id,
                    status,
                    json.dumps(self.redact(arguments), ensure_ascii=False),
                    detail[:1000],
                    datetime.now(UTC).isoformat(),
                ),
            )

    def audit_entries(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM tool_audit ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) | {"arguments": json.loads(row["arguments"])} for row in rows]


class ToolExecutor:
    def __init__(
        self,
        security: ToolSecurityStore,
        registry: ToolRegistry | None = None,
        manager: MCPManager | None = None,
    ):
        self.security = security
        self.registry = registry or tool_registry
        self.manager = manager or mcp_manager

    def _authorize(self, tool: ToolDefinition, consent: str | None) -> None:
        stored = self.security.permission(tool.id)
        if consent == "deny":
            self.security.set_permission(tool.id, "deny")
            raise PermissionError("Tool permission denied.")
        if consent == "always":
            self.security.set_permission(tool.id, "allow")
            return
        if consent == "once":
            return
        if stored == "allow":
            return
        if stored == "deny":
            raise PermissionError("Tool permission denied.")
        raise PermissionRequired("Tool requires user confirmation.")

    def _safe_file(self, raw_path: str) -> Path:
        target = Path(raw_path).expanduser().resolve()
        allowed = [Path(item) for item in self.security.scopes()]
        if not any(target == root or root in target.parents for root in allowed):
            raise PermissionError("Path is outside the user-approved filesystem scopes.")
        return target

    async def execute(
        self, tool_id: str, arguments: dict[str, Any], consent: str | None = None
    ) -> dict[str, Any]:
        tool = self.registry.get(tool_id)
        if tool is None:
            raise KeyError(tool_id)
        try:
            self._authorize(tool, consent)
            if tool_id == "local:file.read":
                path = self._safe_file(str(arguments.get("path", "")))
                if not path.is_file() or path.stat().st_size > 1_000_000:
                    raise ValueError("File must exist and be no larger than 1 MB.")
                result = {"content": path.read_text(encoding="utf-8", errors="replace")}
            elif tool.source == "mcp":
                client = self.manager.clients.get(tool.server_id)
                if client is None:
                    raise RuntimeError("MCP server is not connected.")
                result = await client.call_tool(tool.name, arguments)
            else:
                raise RuntimeError("Tool has no executor.")
            self.security.audit(tool_id, "allowed", arguments)
            return result
        except PermissionRequired:
            self.security.audit(tool_id, "confirmation_required", arguments)
            raise
        except PermissionError as exc:
            self.security.audit(tool_id, "denied", arguments, str(exc))
            raise
        except Exception as exc:
            self.security.audit(tool_id, "error", arguments, str(exc))
            raise


tool_registry.register(
    ToolDefinition(
        id="local:file.read",
        name="Yerel dosya oku",
        description="Kullanıcının izin verdiği bir klasördeki küçük metin dosyasını okur.",
        input_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
        risk="read",
    )
)
tool_security_store = ToolSecurityStore()
tool_executor = ToolExecutor(tool_security_store, tool_registry, mcp_manager)
