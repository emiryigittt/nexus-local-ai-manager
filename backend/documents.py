"""Private SQLite full-text knowledge base for user-provided documents."""

from __future__ import annotations

import re
import sqlite3
import uuid
from array import array
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app_paths import database_path, ensure_data_dirs


class DocumentRepository:
    def __init__(self, path: Path | None = None):
        self.path = path or database_path()
        if path is None:
            ensure_data_dirs()
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL,
                    source_type TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    position INTEGER NOT NULL, content TEXT NOT NULL
                );
                CREATE VIRTUAL TABLE IF NOT EXISTS document_chunks_fts USING fts5(
                    chunk_id UNINDEXED, document_id UNINDEXED, content
                );
                """
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(document_chunks)")
            }
            if "embedding" not in columns:
                connection.execute("ALTER TABLE document_chunks ADD COLUMN embedding BLOB")
            if "embedding_model" not in columns:
                connection.execute("ALTER TABLE document_chunks ADD COLUMN embedding_model TEXT")

    @staticmethod
    def chunks(text: str, size: int = 1200, overlap: int = 160) -> list[str]:
        normalized = re.sub(r"\r\n?", "\n", text).strip()
        if not normalized:
            return []
        result: list[str] = []
        start = 0
        while start < len(normalized):
            end = min(len(normalized), start + size)
            if end < len(normalized):
                boundary = max(
                    normalized.rfind("\n", start, end),
                    normalized.rfind(". ", start, end),
                )
                if boundary > start + size // 2:
                    end = boundary + 1
            result.append(normalized[start:end].strip())
            if end >= len(normalized):
                break
            start = max(start + 1, end - overlap)
        return [item for item in result if item]

    def add(self, name: str, content: str, source_type: str = "text") -> str:
        identifier = str(uuid.uuid4())
        chunks = self.chunks(content)
        if not chunks:
            raise ValueError("Document has no readable text.")
        with self._connect() as connection:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(
                "INSERT INTO documents(id, name, source_type, created_at) VALUES (?, ?, ?, ?)",
                (
                    identifier,
                    name.strip()[:240] or "Belge",
                    source_type,
                    datetime.now(UTC).isoformat(),
                ),
            )
            for position, content_chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                connection.execute(
                    "INSERT INTO document_chunks(id, document_id, position, content) VALUES (?, ?, ?, ?)",
                    (chunk_id, identifier, position, content_chunk),
                )
                connection.execute(
                    "INSERT INTO document_chunks_fts(chunk_id, document_id, content) VALUES (?, ?, ?)",
                    (chunk_id, identifier, content_chunk),
                )
        return identifier

    def list(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]

    def chunk_records(self, document_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, position, content FROM document_chunks WHERE document_id = ? ORDER BY position",
                (document_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def set_embeddings(
        self, document_id: str, vectors: list[list[float]], model: str
    ) -> None:
        chunks = self.chunk_records(document_id)
        if len(chunks) != len(vectors):
            raise ValueError("Embedding count does not match document chunks.")
        with self._connect() as connection:
            for chunk, vector in zip(chunks, vectors, strict=True):
                connection.execute(
                    "UPDATE document_chunks SET embedding = ?, embedding_model = ? WHERE id = ?",
                    (array("f", vector).tobytes(), model, chunk["id"]),
                )

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        if len(left) != len(right) or not left:
            return -1.0
        dot = sum(a * b for a, b in zip(left, right, strict=True))
        left_norm = sum(value * value for value in left) ** 0.5
        right_norm = sum(value * value for value in right) ** 0.5
        return dot / (left_norm * right_norm) if left_norm and right_norm else -1.0

    def search(
        self,
        query: str,
        limit: int = 5,
        *,
        query_vector: list[float] | None = None,
        embedding_model: str = "",
    ) -> list[dict[str, Any]]:
        if query_vector and embedding_model:
            with self._connect() as connection:
                rows = connection.execute(
                    """SELECT d.name, d.source_type, c.position, c.content, c.embedding
                    FROM document_chunks c JOIN documents d ON d.id = c.document_id
                    WHERE c.embedding IS NOT NULL AND c.embedding_model = ?""",
                    (embedding_model,),
                ).fetchall()
            ranked = []
            for row in rows:
                vector = array("f")
                vector.frombytes(row["embedding"])
                item = dict(row)
                item.pop("embedding", None)
                item["score"] = self._cosine(query_vector, list(vector))
                ranked.append(item)
            if ranked:
                return sorted(ranked, key=lambda item: item["score"], reverse=True)[:limit]
        tokens = re.findall(r"[\wÀ-ž]+", query, flags=re.UNICODE)[:12]
        if not tokens:
            return []
        expression = " OR ".join(f'"{token}"' for token in tokens)
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT d.name, d.source_type, c.position, c.content,
                bm25(document_chunks_fts) score FROM document_chunks_fts f
                JOIN document_chunks c ON c.id = f.chunk_id
                JOIN documents d ON d.id = f.document_id
                WHERE document_chunks_fts MATCH ? ORDER BY score LIMIT ?""",
                (expression, limit),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete(self, document_id: str) -> bool:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM document_chunks_fts WHERE document_id = ?", (document_id,)
            )
            connection.execute("PRAGMA foreign_keys = ON")
            cursor = connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return cursor.rowcount > 0


document_repository = DocumentRepository()
