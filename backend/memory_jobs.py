"""Content-free, durable status for background memory extraction (one latest job)."""

import sqlite3
import uuid
from datetime import UTC, datetime

from backend.app_paths import database_path


class MemoryJobStatus:
    def __init__(self, path=None):
        self.path = path or database_path()

    def start(self):
        identifier = str(uuid.uuid4())
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS memory_job_status (slot INTEGER PRIMARY KEY, id TEXT, state TEXT, count INTEGER, updated TEXT)")
            db.execute("INSERT OR REPLACE INTO memory_job_status VALUES (1, ?, 'running', 0, ?)",
                       (identifier, datetime.now(UTC).isoformat()))
        return identifier

    def finish(self, identifier, state, count=0):
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE memory_job_status SET state=?, count=?, updated=? WHERE id=?",
                       (state, count, datetime.now(UTC).isoformat(), identifier))

    def latest(self):
        if not self.path.exists():
            return None
        try:
            with sqlite3.connect(f"file:{self.path}?mode=ro", uri=True) as db:
                db.row_factory = sqlite3.Row
                row = db.execute("SELECT state,count,updated FROM memory_job_status WHERE slot=1").fetchone()
                return dict(row) if row else None
        except sqlite3.OperationalError:
            return None


memory_job_status = MemoryJobStatus()
