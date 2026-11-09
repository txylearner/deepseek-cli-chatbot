"""会话仓库：会话与消息的唯一读写入口。

路由层和 Service 只依赖这里的接口，不写任何 SQL。
以后要换成 MySQL / PostgreSQL，只要再实现一个同名方法的类，
再把 app.py 里的构造换掉即可。

表结构（与 db/schema.py 一致）：
    sessions(id, created_at, updated_at)
    messages(id, session_id → sessions.id, role, content, created_at)
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from ..core.prompts import SYSTEM_PROMPT
from ..db.connection import transaction, utc_now_iso
from ..db.schema import init_schema
from ..models.schemas import Message


class SessionRepository(Protocol):
    """仓库接口：描述“会话存储”必须提供的能力。"""

    def get_or_create(self, session_id: str) -> list[Message]: ...

    def exists(self, session_id: str) -> bool: ...

    def list_ids(self) -> list[str]: ...

    def messages(self, session_id: str) -> list[Message] | None: ...

    def add_message(self, session_id: str, role: str, content: str) -> None: ...

    def drop_last_message(self, session_id: str) -> None: ...

    def clear(self, session_id: str) -> bool: ...

    def reset(self) -> None: ...

    def build_messages(self, session_id: str) -> list[Message]: ...


class SQLiteSessionRepository:
    """把会话与消息持久化到 SQLite 文件。"""

    def __init__(self, db_path: str | Path = "chat.db") -> None:
        self._db_path = str(db_path)
        init_schema(self._db_path)

    # ---------- 查询 ----------

    def get_or_create(self, session_id: str) -> list[Message]:
        now = utc_now_iso()
        with transaction(self._db_path) as connection:
            connection.execute(
                "INSERT OR IGNORE INTO sessions (id, created_at, updated_at) "
                "VALUES (?, ?, ?)",
                (session_id, now, now),
            )
        return self.messages(session_id) or []

    def exists(self, session_id: str) -> bool:
        with transaction(self._db_path) as connection:
            row = connection.execute(
                "SELECT 1 FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return row is not None

    def list_ids(self) -> list[str]:
        with transaction(self._db_path) as connection:
            rows = connection.execute(
                "SELECT id FROM sessions ORDER BY created_at, rowid"
            ).fetchall()
        return [row["id"] for row in rows]

    def messages(self, session_id: str) -> list[Message] | None:
        with transaction(self._db_path) as connection:
            exists = connection.execute(
                "SELECT 1 FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if exists is None:
                return None
            rows = connection.execute(
                "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]

    # ---------- 写入 ----------

    def add_message(self, session_id: str, role: str, content: str) -> None:
        now = utc_now_iso()
        with transaction(self._db_path) as connection:
            connection.execute(
                "INSERT OR IGNORE INTO sessions (id, created_at, updated_at) "
                "VALUES (?, ?, ?)",
                (session_id, now, now),
            )
            connection.execute(
                "INSERT INTO messages (session_id, role, content, created_at) "
                "VALUES (?, ?, ?, ?)",
                (session_id, role, content, now),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )

    def drop_last_message(self, session_id: str) -> None:
        """删掉最后一条消息，用于模型调用失败时回滚刚写入的提问。"""
        with transaction(self._db_path) as connection:
            connection.execute(
                "DELETE FROM messages WHERE id = ("
                "  SELECT id FROM messages WHERE session_id = ? ORDER BY id DESC LIMIT 1"
                ")",
                (session_id,),
            )

    def clear(self, session_id: str) -> bool:
        """删除会话；消息通过外键 ON DELETE CASCADE 一起删除。"""
        with transaction(self._db_path) as connection:
            cursor = connection.execute(
                "DELETE FROM sessions WHERE id = ?", (session_id,)
            )
        return cursor.rowcount > 0

    def reset(self) -> None:
        """清空全部数据，测试之间用它隔离状态。"""
        with transaction(self._db_path) as connection:
            connection.execute("DELETE FROM messages")
            connection.execute("DELETE FROM sessions")

    # ---------- 给模型用 ----------

    def build_messages(self, session_id: str) -> list[Message]:
        history = self.messages(session_id) or []
        return [{"role": "system", "content": SYSTEM_PROMPT}, *history]
