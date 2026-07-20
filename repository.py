from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Optional


@dataclass
class Todo:
    id: int
    title: str
    done: bool
    created_at: str


class TodoRepository:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self):
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT    NOT NULL,
                done       INTEGER NOT NULL DEFAULT 0,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        self._conn.commit()

    def create(self, title: str) -> Todo:
        cur = self._conn.execute(
            "INSERT INTO todos (title) VALUES (?) RETURNING id, title, done, created_at",
            (title,),
        )
        row = cur.fetchone()
        self._conn.commit()
        return Todo(id=row["id"], title=row["title"], done=bool(row["done"]), created_at=row["created_at"])

    def list_all(self) -> list[Todo]:
        rows = self._conn.execute(
            "SELECT id, title, done, created_at FROM todos ORDER BY id"
        ).fetchall()
        return [Todo(id=r["id"], title=r["title"], done=bool(r["done"]), created_at=r["created_at"]) for r in rows]

    def complete(self, todo_id: int) -> Optional[Todo]:
        cur = self._conn.execute(
            "UPDATE todos SET done = 1 WHERE id = ? RETURNING id, title, done, created_at",
            (todo_id,),
        )
        row = cur.fetchone()
        self._conn.commit()
        if row is None:
            return None
        return Todo(id=row["id"], title=row["title"], done=bool(row["done"]), created_at=row["created_at"])

    def delete(self, todo_id: int) -> bool:
        cur = self._conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        self._conn.commit()
        return cur.rowcount > 0
