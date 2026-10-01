"""Explicit, user-controlled personal memory store."""

from __future__ import annotations

import re
import sqlite3
import uuid
from array import array
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app_paths import database_path, ensure_data_dirs

MEMORY_TYPES = {"preference", "fact", "goal", "instruction", "project_decision"}
MEMORY_STATUSES = {"candidate", "active", "superseded", "disabled"}


class MemoryRepository:
    def __init__(self, path: Path | None = None):
        self.path = path or database_path()
        if path is None:
            ensure_data_dirs()
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY, content TEXT NOT NULL, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1)"""
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(memories)")}
            if "memory_type" not in columns:
                connection.execute(
                    "ALTER TABLE memories ADD COLUMN memory_type TEXT NOT NULL DEFAULT 'fact'"
                )
            if "scope" not in columns:
                connection.execute(
                    "ALTER TABLE memories ADD COLUMN scope TEXT NOT NULL DEFAULT 'global'"
                )
            if "project_id" not in columns:
                connection.execute("ALTER TABLE memories ADD COLUMN project_id TEXT")
            if "source_conversation_id" not in columns:
                connection.execute(
                    "ALTER TABLE memories ADD COLUMN source_conversation_id TEXT"
                )
            if "source_message_id" not in columns:
                connection.execute("ALTER TABLE memories ADD COLUMN source_message_id TEXT")
            additions = {
                "confidence": "REAL NOT NULL DEFAULT 1.0",
                "importance": "REAL NOT NULL DEFAULT 0.5",
                "last_used_at": "TEXT",
                "expires_at": "TEXT",
                "pinned": "INTEGER NOT NULL DEFAULT 0",
            }
            for column, definition in additions.items():
                if column not in columns:
                    connection.execute(
                        f"ALTER TABLE memories ADD COLUMN {column} {definition}"
                    )
            if "status" not in columns:
                connection.execute(
                    "ALTER TABLE memories ADD COLUMN status TEXT NOT NULL DEFAULT 'active'"
                )
            if "supersedes_id" not in columns:
                connection.execute("ALTER TABLE memories ADD COLUMN supersedes_id TEXT")
            if "memory_key" not in columns:
                connection.execute("ALTER TABLE memories ADD COLUMN memory_key TEXT")
            if "embedding" not in columns:
                connection.execute("ALTER TABLE memories ADD COLUMN embedding BLOB")
            if "embedding_model" not in columns:
                connection.execute("ALTER TABLE memories ADD COLUMN embedding_model TEXT")
            connection.execute(
                """CREATE TABLE IF NOT EXISTS memory_versions (
                id TEXT PRIMARY KEY, memory_id TEXT NOT NULL, version INTEGER NOT NULL,
                content TEXT NOT NULL, memory_type TEXT NOT NULL, scope TEXT NOT NULL,
                project_id TEXT, status TEXT NOT NULL, created_at TEXT NOT NULL)"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS memory_profile (
                id INTEGER PRIMARY KEY CHECK(id = 1), summary TEXT NOT NULL,
                updated_at TEXT NOT NULL)"""
            )

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _validate_type(memory_type: str) -> str:
        normalized = memory_type.strip().casefold()
        if normalized not in MEMORY_TYPES:
            raise ValueError(f"Unknown memory type: {memory_type}")
        return normalized

    def add(
        self,
        content: str,
        memory_type: str = "fact",
        scope: str = "global",
        project_id: str | None = None,
        source_conversation_id: str | None = None,
        source_message_id: str | None = None,
        confidence: float = 1.0,
        importance: float = 0.5,
        expires_at: str | None = None,
        pinned: bool = False,
        status: str = "active",
        supersedes_id: str | None = None,
        memory_key: str | None = None,
    ) -> str:
        clean = " ".join(content.split())
        if not clean:
            raise ValueError("Memory cannot be empty.")
        identifier = str(uuid.uuid4())
        normalized_type = self._validate_type(memory_type)
        if scope not in {"global", "project"}:
            raise ValueError("Memory scope must be global or project.")
        if scope == "project" and not project_id:
            raise ValueError("Project memories require a project id.")
        if scope == "global":
            project_id = None
        confidence = min(max(float(confidence), 0.0), 1.0)
        importance = min(max(float(importance), 0.0), 1.0)
        if status not in MEMORY_STATUSES:
            raise ValueError("Unknown memory status.")
        memory_key = self.normalize_key(memory_key)
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO memories
                (id, content, created_at, updated_at, memory_type, scope, project_id,
                source_conversation_id, source_message_id, confidence, importance,
                expires_at, pinned, status, supersedes_id, memory_key)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    identifier,
                    clean[:2000],
                    now,
                    now,
                    normalized_type,
                    scope,
                    project_id,
                    source_conversation_id,
                    source_message_id,
                    confidence,
                    importance,
                    expires_at,
                    int(pinned),
                    status,
                    supersedes_id,
                    memory_key,
                ),
            )
        return identifier

    @staticmethod
    def normalize_key(memory_key: str | None) -> str | None:
        if not memory_key:
            return None
        normalized = re.sub(r"[^a-z0-9_.-]+", "_", memory_key.casefold()).strip("_.-")
        return normalized[:120] or None

    @staticmethod
    def _same_content(left: str, right: str) -> bool:
        def normalize(value: str) -> str:
            return re.sub(r"[^\w]+", " ", value.casefold()).strip()

        return normalize(left) == normalize(right)

    def add_candidate(
        self,
        content: str,
        memory_type: str,
        memory_key: str,
        *,
        project_id: str | None = None,
        source_conversation_id: str | None = None,
        confidence: float = 1.0,
        importance: float = 0.5,
    ) -> tuple[str, str]:
        scope = "project" if project_id else "global"
        normalized_key = self.normalize_key(memory_key)
        with self._connect() as connection:
            existing = connection.execute(
                """SELECT * FROM memories WHERE memory_key = ? AND scope = ?
                AND COALESCE(project_id, '') = COALESCE(?, '')
                AND status IN ('candidate', 'active') ORDER BY updated_at DESC LIMIT 1""",
                (normalized_key, scope, project_id),
            ).fetchone()
        if existing and self._same_content(existing["content"], content):
            return str(existing["id"]), "duplicate"
        identifier = self.add(
            content,
            memory_type,
            scope,
            project_id,
            source_conversation_id=source_conversation_id,
            confidence=confidence,
            importance=importance,
            status="candidate",
            supersedes_id=str(existing["id"]) if existing else None,
            memory_key=normalized_key,
        )
        if existing and existing["status"] == "candidate":
            self.update(
                str(existing["id"]),
                str(existing["content"]),
                enabled=False,
                memory_type=str(existing["memory_type"]),
                scope=str(existing["scope"]),
                project_id=existing["project_id"],
                status="superseded",
            )
        return identifier, "replacement" if existing else "created"

    def activate(self, memory_id: str) -> bool:
        with self._connect() as connection:
            memory = connection.execute(
                "SELECT * FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
        if memory is None:
            return False
        updated = self.update(
            memory_id,
            str(memory["content"]),
            enabled=True,
            memory_type=str(memory["memory_type"]),
            scope=str(memory["scope"]),
            project_id=memory["project_id"],
            status="active",
        )
        if updated and memory["supersedes_id"]:
            with self._connect() as connection:
                connection.execute(
                    """UPDATE memories SET status = 'superseded', enabled = 0,
                    updated_at = ? WHERE id = ?""",
                    (datetime.now(UTC).isoformat(), memory["supersedes_id"]),
                )
        return updated

    def save_introduction(self, entries: dict[str, tuple[str, str]]) -> None:
        """Commit explicitly reviewed profile answers together, preserving versions.

        Missing fields are unchanged. These are ordinary memories, so disabling,
        editing or forgetting them in the memory manager also changes the profile.
        """
        clean_entries = []
        for key, (content, memory_type) in entries.items():
            if not key.startswith("user.") or self.normalize_key(key) != key:
                raise ValueError("Invalid introduction key.")
            clean = " ".join(content.split())
            if not clean or len(clean) > 500:
                raise ValueError("Invalid introduction answer.")
            clean_entries.append((key, clean, self._validate_type(memory_type)))
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            for key, content, memory_type in clean_entries:
                existing = connection.execute(
                    """SELECT * FROM memories WHERE memory_key = ? AND scope = 'global'
                    AND status = 'active' ORDER BY updated_at DESC LIMIT 1""", (key,),
                ).fetchone()
                if existing and existing["enabled"] and self._same_content(existing["content"], content):
                    continue
                # Supersede all previous active/candidate answers for this field.
                connection.execute(
                    """UPDATE memories SET status = 'superseded', enabled = 0, updated_at = ?
                    WHERE memory_key = ? AND scope = 'global' AND status IN ('active', 'candidate')""",
                    (now, key),
                )
                connection.execute(
                    """INSERT INTO memories
                    (id, content, created_at, updated_at, memory_type, scope,
                    confidence, importance, pinned, status, supersedes_id, memory_key)
                    VALUES (?, ?, ?, ?, ?, 'global', 1, 0.9, 1, 'active', ?, ?)""",
                    (str(uuid.uuid4()), content, now, now, memory_type,
                     existing["id"] if existing else None, key),
                )

    def list(self, enabled_only: bool = False) -> list[dict[str, Any]]:
        clause = " WHERE enabled = 1" if enabled_only else ""
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT * FROM memories{clause} ORDER BY updated_at DESC"
            ).fetchall()
        values = []
        for row in rows:
            item = dict(row)
            item.pop("embedding", None)
            values.append(item)
        return values

    def for_context(self, project_id: str | None = None) -> list[dict[str, Any]]:
        now = datetime.now(UTC).isoformat()
        with self._connect() as connection:
            if project_id:
                rows = connection.execute(
                    """SELECT * FROM memories WHERE enabled = 1 AND status = 'active'
                    AND (expires_at IS NULL OR expires_at > ?)
                    AND (scope = 'global' OR (scope = 'project' AND project_id = ?))
                    ORDER BY pinned DESC, importance DESC, updated_at DESC""",
                    (now, project_id),
                ).fetchall()
            else:
                rows = connection.execute(
                    """SELECT * FROM memories WHERE enabled = 1 AND status = 'active'
                    AND scope = 'global'
                    AND (expires_at IS NULL OR expires_at > ?)
                    ORDER BY pinned DESC, importance DESC, updated_at DESC""",
                    (now,),
                ).fetchall()
        return [dict(row) for row in rows]

    def mark_used(self, memory_ids: list[str]) -> None:
        if not memory_ids:
            return
        placeholders = ",".join("?" for _ in memory_ids)
        with self._connect() as connection:
            connection.execute(
                f"UPDATE memories SET last_used_at = ? WHERE id IN ({placeholders})",
                (datetime.now(UTC).isoformat(), *memory_ids),
            )

    def set_embeddings(
        self, values: list[tuple[str, list[float]]], embedding_model: str
    ) -> None:
        with self._connect() as connection:
            for memory_id, vector in values:
                connection.execute(
                    "UPDATE memories SET embedding = ?, embedding_model = ? WHERE id = ?",
                    (array("f", vector).tobytes(), embedding_model, memory_id),
                )

    def update(
        self,
        memory_id: str,
        content: str,
        enabled: bool = True,
        memory_type: str = "fact",
        scope: str = "global",
        project_id: str | None = None,
        status: str = "active",
        confidence: float | None = None,
        importance: float | None = None,
        pinned: bool | None = None,
        expires_at: str | None = None,
    ) -> bool:
        clean = " ".join(content.split())
        if not clean:
            raise ValueError("Memory cannot be empty.")
        normalized_type = self._validate_type(memory_type)
        if scope not in {"global", "project"}:
            raise ValueError("Memory scope must be global or project.")
        if scope == "project" and not project_id:
            raise ValueError("Project memories require a project id.")
        if scope == "global":
            project_id = None
        if status not in MEMORY_STATUSES:
            raise ValueError("Unknown memory status.")
        with self._connect() as connection:
            current = connection.execute(
                "SELECT * FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
            if current is None:
                return False
            confidence = (
                float(current["confidence"]) if confidence is None else min(max(confidence, 0), 1)
            )
            importance = (
                float(current["importance"]) if importance is None else min(max(importance, 0), 1)
            )
            pinned = bool(current["pinned"]) if pinned is None else pinned
            if expires_at is None:
                expires_at = current["expires_at"]
            version = connection.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 FROM memory_versions WHERE memory_id = ?",
                (memory_id,),
            ).fetchone()[0]
            connection.execute(
                """INSERT INTO memory_versions
                (id, memory_id, version, content, memory_type, scope, project_id, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()), memory_id, version, current["content"],
                    current["memory_type"], current["scope"], current["project_id"],
                    current["status"], datetime.now(UTC).isoformat(),
                ),
            )
            cursor = connection.execute(
                """UPDATE memories SET content = ?, enabled = ?, memory_type = ?, scope = ?,
                project_id = ?, status = ?, confidence = ?, importance = ?, pinned = ?,
                expires_at = ?, embedding = NULL, embedding_model = NULL,
                updated_at = ? WHERE id = ?""",
                (
                    clean[:2000],
                    int(enabled),
                    normalized_type,
                    scope,
                    project_id,
                    status,
                    confidence,
                    importance,
                    int(pinned),
                    expires_at,
                    datetime.now(UTC).isoformat(),
                    memory_id,
                ),
            )
        return cursor.rowcount > 0

    def profile_summary(self) -> str:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT summary FROM memory_profile WHERE id = 1"
            ).fetchone()
        return str(row["summary"]) if row else ""

    def set_profile_summary(self, summary: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO memory_profile(id, summary, updated_at) VALUES (1, ?, ?)
                ON CONFLICT(id) DO UPDATE SET summary=excluded.summary,
                updated_at=excluded.updated_at""",
                (summary.strip()[:8000], datetime.now(UTC).isoformat()),
            )

    def delete_all(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM memory_versions")
            connection.execute("DELETE FROM memories")
            connection.execute("DELETE FROM memory_profile")

    def versions(self, memory_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT * FROM memory_versions WHERE memory_id = ?
                ORDER BY version DESC""",
                (memory_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete(self, memory_id: str) -> bool:
        with self._connect() as connection:
            connection.execute("DELETE FROM memory_versions WHERE memory_id = ?", (memory_id,))
            cursor = connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        return cursor.rowcount > 0


memory_repository = MemoryRepository()
