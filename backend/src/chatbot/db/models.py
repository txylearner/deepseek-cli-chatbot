"""SQLAlchemy 2.x 声明式模型：把 ORM 映射到已有的 SQLite 表。

表结构与第 4 次作业的 DDL 一一对应（见 README「模型与数据表对应关系」）：

    sessions(id, created_at, updated_at)
    messages(id, session_id -> sessions.id, role, content, created_at)

字段类型用 Text / Integer，生成的 DDL 与旧库保持同样的类型亲和性，
所以启动时的 create_all(checkfirst=True) 不会改动旧表，也不会丢数据。
"""

from __future__ import annotations

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """所有 ORM 模型的基类，建表语句由它的 metadata 生成。"""


class ChatSession(Base):
    """会话表：一行一个会话。"""

    __tablename__ = "sessions"
    __table_args__ = (
        # 与旧库同名同列，create_all 时按名字判断是否已存在
        Index("idx_sessions_updated", "updated_at"),
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        # 删除会话时交给数据库的 ON DELETE CASCADE，不逐条加载消息
        passive_deletes=True,
        order_by="ChatMessage.id",
    )


class ChatMessage(Base):
    """消息表：一行一句话，role 只有 user / assistant / system。"""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')", name="ck_messages_role"
        ),
        Index("idx_messages_session", "session_id", "id"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        Text, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)

    session: Mapped[ChatSession] = relationship(back_populates="messages")
