"""SQLite-backed local conversation history."""

from __future__ import annotations

import json
import re
import sqlite3
import threading
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app_paths import database_path, ensure_data_dirs


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ConversationRepository:
    def __init__(self, path: Path | None = None):
        self.path = path or database_path()
        self._lock = threading.RLock()
        if path is None:
            ensure_data_dirs()
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER NOT NULL
                );
                INSERT INTO schema_version(version)
                SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM schema_version);

                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    provider_id TEXT NOT NULL DEFAULT '',
                    model_id TEXT NOT NULL DEFAULT '',
                    pinned INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK(role IN ('system', 'user', 'assistant', 'tool')),
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS messages_conversation_idx
                    ON messages(conversation_id, created_at);
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                    message_id UNINDEXED, conversation_id UNINDEXED, content
                );
                CREATE TABLE IF NOT EXISTS conversation_summaries (
                    kind TEXT NOT NULL CHECK(kind IN ('conversation', 'project')),
                    scope_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    source_message_count INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(kind, scope_id)
                );
                """
            )

    def create(
        self,
        title: str,
        *,
        provider_id: str = "",
        model_id: str = "",
        conversation_id: str | None = None,
    ) -> str:
        identifier = conversation_id or str(uuid.uuid4())
        timestamp = _now()
        clean_title = " ".join(title.split())[:80] or "Yeni konuşma"
        with self._lock, self._connection() as connection:
            connection.execute(
                """INSERT OR IGNORE INTO conversations
                (id, title, provider_id, model_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (identifier, clean_title, provider_id, model_id, timestamp, timestamp),
            )
        return identifier

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        identifier = str(uuid.uuid4())
        timestamp = _now()
        with self._lock, self._connection() as connection:
            connection.execute(
                """INSERT INTO messages
                (id, conversation_id, role, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    identifier,
                    conversation_id,
                    role,
                    content,
                    json.dumps(metadata or {}, ensure_ascii=False),
                    timestamp,
                ),
            )
            connection.execute(
                "INSERT INTO messages_fts(message_id, conversation_id, content) VALUES (?, ?, ?)",
                (identifier, conversation_id, content),
            )
            connection.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (timestamp, conversation_id),
            )
        return identifier

    def list(self, query: str = "", limit: int = 100) -> list[dict[str, Any]]:
        with self._connection() as connection:
            if query.strip():
                tokens = re.findall(r"\w+", query, flags=re.UNICODE)[:24]
                if not tokens:
                    return []
                expression = " AND ".join(f'"{token}"' for token in tokens)
                rows = connection.execute(
                    """SELECT DISTINCT c.* FROM conversations c
                    JOIN messages_fts f ON f.conversation_id = c.id
                    WHERE messages_fts MATCH ?
                    ORDER BY c.pinned DESC, c.updated_at DESC LIMIT ?""",
                    (expression, limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    """SELECT * FROM conversations
                    ORDER BY pinned DESC, updated_at DESC LIMIT ?""",
                    (limit,),
                ).fetchall()
        return [dict(row) for row in rows]

    def messages(self, conversation_id: str) -> list[dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at, rowid",
                (conversation_id,),
            ).fetchall()
        return [dict(row) | {"metadata": json.loads(row["metadata"])} for row in rows]

    def summary(self, kind: str, scope_id: str) -> dict[str, Any] | None:
        if kind not in {"conversation", "project"}:
            raise ValueError("Summary kind must be conversation or project.")
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM conversation_summaries WHERE kind = ? AND scope_id = ?",
                (kind, scope_id),
            ).fetchone()
        return dict(row) if row else None

    def upsert_summary(
        self, kind: str, scope_id: str, summary: str, source_message_count: int
    ) -> None:
        if kind not in {"conversation", "project"}:
            raise ValueError("Summary kind must be conversation or project.")
        clean = summary.strip()[:8000]
        if not clean:
            raise ValueError("Summary cannot be empty.")
        with self._connection() as connection:
            connection.execute(
                """INSERT INTO conversation_summaries
                (kind, scope_id, summary, source_message_count, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(kind, scope_id) DO UPDATE SET summary=excluded.summary,
                source_message_count=excluded.source_message_count,
                updated_at=excluded.updated_at""",
                (kind, scope_id, clean, source_message_count, _now()),
            )

    def update(self, conversation_id: str, *, title: str | None = None, pinned: bool | None = None) -> bool:
        changes: list[str] = []
        values: list[Any] = []
        if title is not None:
            changes.append("title = ?")
            values.append(" ".join(title.split())[:80] or "Yeni konuşma")
        if pinned is not None:
            changes.append("pinned = ?")
            values.append(int(pinned))
        if not changes:
            return False
        changes.append("updated_at = ?")
        values.append(_now())
        values.append(conversation_id)
        with self._lock, self._connection() as connection:
            cursor = connection.execute(
                f"UPDATE conversations SET {', '.join(changes)} WHERE id = ?", values
            )
        return cursor.rowcount > 0

    def delete(self, conversation_id: str) -> bool:
        with self._lock, self._connection() as connection:
            connection.execute(
                "DELETE FROM messages_fts WHERE conversation_id = ?", (conversation_id,)
            )
            connection.execute(
                "DELETE FROM conversation_summaries WHERE kind = 'conversation' AND scope_id = ?",
                (conversation_id,),
            )
            cursor = connection.execute(
                "DELETE FROM conversations WHERE id = ?", (conversation_id,)
            )
        return cursor.rowcount > 0


conversation_repository = ConversationRepository()
