import sqlite3
from contextlib import contextmanager
from pathlib import Path
from backend.models import CallResult


class Store:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS calls (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, body TEXT NOT NULL)")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            with db:
                yield db
        finally:
            db.close()

    def save(self, call: CallResult):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO calls VALUES (?, ?, ?)", (call.id, call.created_at, call.model_dump_json()))

    def get(self, call_id: str) -> CallResult | None:
        with self.connect() as db:
            row = db.execute("SELECT body FROM calls WHERE id = ?", (call_id,)).fetchone()
        return CallResult.model_validate_json(row[0]) if row else None

    def list(self, limit: int = 100) -> list[CallResult]:
        with self.connect() as db:
            rows = db.execute("SELECT body FROM calls ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [CallResult.model_validate_json(row[0]) for row in rows]

    def interrupt_pending(self):
        with self.connect() as db:
            rows = db.execute("SELECT body FROM calls").fetchall()
            for (body,) in rows:
                call = CallResult.model_validate_json(body)
                if call.status in {"queued", "processing"}:
                    call.status = "interrupted"
                    call.error = "Server restarted before processing finished. Upload again to retry."
                    db.execute("UPDATE calls SET body = ? WHERE id = ?", (call.model_dump_json(), call.id))
