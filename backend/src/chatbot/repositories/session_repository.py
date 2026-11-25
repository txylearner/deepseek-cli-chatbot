"""会话仓库：会话与消息的唯一读写入口。

路由层和 Service 只依赖这里的接口，不写任何 SQL。
实现使用 SQLAlchemy 2.x ORM：查询用 select() 表达式，写入用 Session 工作单元，
每次操作都显式打开和关闭 Session（见 db/engine.py 的 session_scope）。

表结构（与 db/models.py 一致）：
    sessions(id, created_at, updated_at)
    messages(id, session_id -> sessions.id, role, content, created_at)
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol

from sqlalchemy import delete, func, literal_column, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session as OrmSession

from ..core.clock import utc_now_iso
from ..core.exceptions import StorageError
from ..core.prompts import SYSTEM_PROMPT
from ..db.engine import create_session_factory, get_engine, session_scope
from ..db.models import ChatMessage, ChatSession
from ..db.schema import init_schema
from ..models.schemas import Message


class SessionRepository(Protocol):
    """仓库接口：描述“会话存储”必须提供的能力。"""

    def get_or_create(self, session_id: str) -> list[Message]: ...

    def exists(self, session_id: str) -> bool: ...

    def list_ids(self) -> list[str]: ...

    def overview(self) -> list[dict[str, object]]: ...

    def messages(
        self, session_id: str, keyword: str | None = None
    ) -> list[Message] | None: ...

    def add_message(self, session_id: str, role: str, content: str) -> None: ...

    def append_turn(
        self, session_id: str, user_content: str, assistant_content: str
    ) -> None: ...

    def clear(self, session_id: str) -> bool: ...

    def reset(self) -> None: ...

    def build_messages(self, session_id: str) -> list[Message]: ...


class SQLiteSessionRepository:
    """用 ORM 把会话与消息持久化到 SQLite 文件。"""

    def __init__(self, db_path: str | Path = "chat.db") -> None:
        self._db_path = str(db_path)
        init_schema(self._db_path)
        self._session_factory = create_session_factory(get_engine(self._db_path))

    # ---------- 工作单元 ----------

    @contextmanager
    def _scope(self) -> Iterator[OrmSession]:
        """一次数据库操作：开 Session -> 提交/回滚 -> 关闭，并翻译底层异常。"""
        try:
            with session_scope(self._session_factory) as session:
                yield session
        except SQLAlchemyError as exc:
            raise StorageError(f"数据库操作失败：{type(exc).__name__}") from exc

    # ---------- 查询 ----------

    def get_or_create(self, session_id: str) -> list[Message]:
        now = utc_now_iso()
        with self._scope() as session:
            self._ensure_session(session, session_id, now)
        return self.messages(session_id) or []

    def exists(self, session_id: str) -> bool:
        with self._scope() as session:
            return session.get(ChatSession, session_id) is not None

    def list_ids(self) -> list[str]:
        stmt = select(ChatSession.id).order_by(
            ChatSession.created_at, literal_column("sessions.rowid")
        )
        with self._scope() as session:
            return list(session.scalars(stmt).all())

    def overview(self) -> list[dict[str, object]]:
        """会话概览：消息条数 + 最近更新时间 + 首条用户消息，供侧边栏显示。

        两个相关子查询（消息数、首条提问）一次取回，前端不需要为每个会话再请求一次。
        同一秒内写入的会话按 SQLite 的 rowid 排序，保证顺序稳定。
        """
        message_count = (
            select(func.count(ChatMessage.id))
            .where(ChatMessage.session_id == ChatSession.id)
            .correlate(ChatSession)
            .scalar_subquery()
        )
        first_user_message = (
            select(ChatMessage.content)
            .where(
                ChatMessage.session_id == ChatSession.id,
                ChatMessage.role == "user",
            )
            .order_by(ChatMessage.id)
            .limit(1)
            .correlate(ChatSession)
            .scalar_subquery()
        )

        stmt = (
            select(
                ChatSession.id,
                ChatSession.updated_at,
                message_count.label("message_count"),
                func.coalesce(first_user_message, "").label("title"),
            )
            .order_by(
                ChatSession.updated_at.desc(),
                literal_column("sessions.rowid").desc(),
            )
        )

        with self._scope() as session:
            rows = session.execute(stmt).all()

        return [
            {
                "id": row.id,
                "title": row.title,
                "message_count": row.message_count,
                "updated_at": row.updated_at,
            }
            for row in rows
        ]

    def messages(
        self, session_id: str, keyword: str | None = None
    ) -> list[Message] | None:
        """会话的历史消息；keyword 非空时只保留内容包含它的消息。

        过滤用 ORM 表达式 ChatMessage.content.contains(keyword, autoescape=True)，
        编译出来是 content LIKE '%' || ? || '%' ESCAPE '/'：
        关键词里的 % 与 _ 会被转义成普通字符，不会当成通配符。
        排序仍然按 id 升序，所以命中结果与完整历史的相对顺序一致。
        """
        keyword = (keyword or "").strip()
        with self._scope() as session:
            if session.get(ChatSession, session_id) is None:
                return None
            stmt = (
                select(ChatMessage.role, ChatMessage.content)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.id)
            )
            if keyword:
                stmt = stmt.where(
                    ChatMessage.content.contains(keyword, autoescape=True)
                )
            rows = session.execute(stmt).all()
        return [{"role": role, "content": content} for role, content in rows]

    # ---------- 写入 ----------

    def add_message(self, session_id: str, role: str, content: str) -> None:
        now = utc_now_iso()
        with self._scope() as session:
            self._ensure_session(session, session_id, now)
            self._insert_message(session, session_id, role, content, now)
            self._touch_session(session, session_id, now)

    def append_turn(
        self, session_id: str, user_content: str, assistant_content: str
    ) -> None:
        """把一轮对话的提问与回复写在同一个事务里。

        两次插入都在同一个 Session 中完成、最后一起提交：
        任何一步失败都会整体回滚，不会留下“只有提问没有回答”的半轮记录。
        """
        now = utc_now_iso()
        with self._scope() as session:
            self._ensure_session(session, session_id, now)
            self._insert_message(session, session_id, "user", user_content, now)
            session.flush()
            self._insert_message(
                session, session_id, "assistant", assistant_content, now
            )
            session.flush()
            self._touch_session(session, session_id, now)

    def clear(self, session_id: str) -> bool:
        """删除会话；消息通过外键 ON DELETE CASCADE 一起删除。"""
        with self._scope() as session:
            stored = session.get(ChatSession, session_id)
            if stored is None:
                return False
            session.delete(stored)
        return True

    def reset(self) -> None:
        """清空全部数据，测试之间用它隔离状态。"""
        with self._scope() as session:
            session.execute(delete(ChatMessage))
            session.execute(delete(ChatSession))

    # ---------- 给模型用 ----------

    def build_messages(self, session_id: str) -> list[Message]:
        history = self.messages(session_id) or []
        return [{"role": "system", "content": SYSTEM_PROMPT}, *history]

    # ---------- 内部：SQLAlchemy 语句 ----------

    def _ensure_session(
        self, session: OrmSession, session_id: str, now: str
    ) -> None:
        """会话不存在就创建；并发下用 SAVEPOINT 兜住主键冲突。"""
        if session.get(ChatSession, session_id) is not None:
            return
        try:
            with session.begin_nested():
                session.add(
                    ChatSession(id=session_id, created_at=now, updated_at=now)
                )
        except IntegrityError:
            # 另一个请求刚好抢先建好了这个会话，本轮继续写消息
            pass

    def _insert_message(
        self,
        session: OrmSession,
        session_id: str,
        role: str,
        content: str,
        created_at: str,
    ) -> None:
        session.add(
            ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                created_at=created_at,
            )
        )

    def _touch_session(
        self, session: OrmSession, session_id: str, now: str
    ) -> None:
        session.execute(
            update(ChatSession)
            .where(ChatSession.id == session_id)
            .values(updated_at=now)
        )
