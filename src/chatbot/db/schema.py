"""数据库结构：表、外键与索引只在这里定义一次。

README 里的 mermaid ER 图必须和这里的 DDL 保持一致。
"""

from __future__ import annotations

from pathlib import Path

from .connection import transaction

DDL = """
CREATE TABLE IF NOT EXISTS sessions (
    id         TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT    NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role       TEXT    NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content    TEXT    NOT NULL,
    created_at TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, id);
CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at);
"""


def init_schema(db_path: str | Path) -> None:
    """运行时自动建表；已存在时什么也不做，可重复执行。"""
    path = Path(db_path)
    if str(db_path) != ":memory:" and path.parent != Path(""):
        path.parent.mkdir(parents=True, exist_ok=True)
    with transaction(db_path) as connection:
        connection.executescript(DDL)
