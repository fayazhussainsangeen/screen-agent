from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


class LongTermMemory:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS facts(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE,
                    value TEXT,
                    timestamp TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT,
                    content TEXT,
                    timestamp TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS command_log(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command TEXT,
                    output TEXT,
                    timestamp TEXT
                )
                """
            )

    def save_fact(self, key: str, value: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO facts(key, value, timestamp)
                VALUES(?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, timestamp=excluded.timestamp
                """,
                (key, value, now),
            )

    def get_fact(self, key: str) -> str | None:
        with self._conn() as conn:
            row = conn.execute("SELECT value FROM facts WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def save_turn(self, role: str, content: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO history(role, content, timestamp) VALUES(?, ?, ?)",
                (role, content, now),
            )

    def get_recent(self, n: int = 50) -> list[tuple[str, str, str]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT role, content, timestamp FROM history ORDER BY id DESC LIMIT ?", (n,)
            ).fetchall()
        return list(reversed(rows))

    def search_history(self, query: str) -> list[tuple[str, str, str]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT role, content, timestamp FROM history WHERE content LIKE ? ORDER BY id DESC LIMIT 50",
                (f"%{query}%",),
            ).fetchall()
        return rows

    def log_command(self, command: str, output: str) -> None:
        now = datetime.utcnow().isoformat()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO command_log(command, output, timestamp) VALUES(?, ?, ?)",
                (command, output, now),
            )
