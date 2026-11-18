"""ORM 存储层：表结构、旧库兼容、重开连接、会话隔离、级联删除。

全部使用 pytest 的 tmp_path 临时数据库，不读写开发者本地的 .env 和 chat.db。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from chatbot.db.engine import dispose_engine
from chatbot.repositories.session_repository import SQLiteSessionRepository

# 第 4 次作业的建表语句：用来模拟“升级前就存在、里面已经有数据”的库
LEGACY_DDL = """
CREATE TABLE sessions (
    id         TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT    NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role       TEXT    NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content    TEXT    NOT NULL,
    created_at TEXT    NOT NULL
);

CREATE INDEX idx_messages_session ON messages(session_id, id);
CREATE INDEX idx_sessions_updated ON sessions(updated_at);
"""


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "chat.db"


@pytest.fixture
def repo(db_path: Path) -> SQLiteSessionRepository:
    return SQLiteSessionRepository(db_path)


def _build_legacy_database(db_path: Path) -> None:
    """用旧 DDL 建库并塞入两条消息，模拟第 4 次作业留下的 chat.db。"""
    with sqlite3.connect(db_path) as connection:
        connection.executescript(LEGACY_DDL)
        connection.execute(
            "INSERT INTO sessions (id, created_at, updated_at) VALUES (?, ?, ?)",
            ("old", "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:01+00:00"),
        )
        connection.executemany(
            "INSERT INTO messages (session_id, role, content, created_at) "
            "VALUES (?, ?, ?, ?)",
            [
                ("old", "user", "升级前的提问", "2026-01-01T00:00:00+00:00"),
                ("old", "assistant", "升级前的回答", "2026-01-01T00:00:01+00:00"),
            ],
        )


def test_orm_creates_the_same_table_layout(db_path: Path, repo) -> None:
    """新建库时，ORM 生成的表结构要和旧库一致：字段、外键、索引、自增。"""
    with sqlite3.connect(db_path) as connection:
        columns = [row[1] for row in connection.execute("PRAGMA table_info(messages)")]
        foreign_keys = connection.execute("PRAGMA foreign_key_list(messages)").fetchall()
        indexes = {row[1] for row in connection.execute("PRAGMA index_list(messages)")}
        ddl = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'messages'"
        ).fetchone()[0]

    assert columns == ["id", "session_id", "role", "content", "created_at"]
    assert any(
        row[2] == "sessions" and row[3] == "session_id" and row[6] == "CASCADE"
        for row in foreign_keys
    )
    assert "idx_messages_session" in indexes
    assert "AUTOINCREMENT" in ddl.upper()
    assert "CHECK" in ddl.upper()


def test_legacy_database_keeps_its_data(db_path: Path) -> None:
    """打开第 4 次作业留下的库：旧记录照常读取，表结构一个字节都没被改。"""
    _build_legacy_database(db_path)
    with sqlite3.connect(db_path) as connection:
        before = connection.execute(
            "SELECT name, sql FROM sqlite_master ORDER BY name"
        ).fetchall()

    repo = SQLiteSessionRepository(db_path)

    assert repo.list_ids() == ["old"]
    assert repo.messages("old") == [
        {"role": "user", "content": "升级前的提问"},
        {"role": "assistant", "content": "升级前的回答"},
    ]

    with sqlite3.connect(db_path) as connection:
        after = connection.execute(
            "SELECT name, sql FROM sqlite_master ORDER BY name"
        ).fetchall()
        message_count = connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0]

    assert after == before
    assert message_count == 2


def test_history_survives_reopening_the_database(db_path: Path) -> None:
    """关掉连接池再重新打开（等价于重启服务），历史仍在。"""
    repo = SQLiteSessionRepository(db_path)
    repo.append_turn("u1", "重启前的问题", "重启前的回答")

    dispose_engine(db_path)
    reopened = SQLiteSessionRepository(db_path)

    assert reopened.list_ids() == ["u1"]
    assert [item["content"] for item in reopened.messages("u1")] == [
        "重启前的问题",
        "重启前的回答",
    ]


def test_sessions_do_not_mix(repo) -> None:
    """两个会话的消息互不干扰。"""
    repo.append_turn("u1", "我是小明", "好的小明")
    repo.append_turn("u2", "我是小红", "好的小红")

    assert [item["content"] for item in repo.messages("u1")] == [
        "我是小明",
        "好的小明",
    ]
    assert [item["content"] for item in repo.messages("u2")] == [
        "我是小红",
        "好的小红",
    ]


def test_get_or_create_is_idempotent(repo) -> None:
    assert repo.get_or_create("u1") == []
    repo.add_message("u1", "user", "只问不答")

    assert repo.get_or_create("u1") == [{"role": "user", "content": "只问不答"}]
    assert repo.list_ids() == ["u1"]


def test_overview_is_built_with_orm_aggregation(repo) -> None:
    """概览用相关子查询算消息数与首条提问，最近更新的会话排在前面。"""
    repo.append_turn("u1", "第一问", "第一答")
    repo.append_turn("u1", "第二问", "第二答")
    repo.append_turn("u2", "另一个会话", "收到")

    overview = repo.overview()

    assert [item["id"] for item in overview] == ["u2", "u1"]
    assert overview[0]["title"] == "另一个会话"
    assert overview[0]["message_count"] == 2
    assert overview[1]["title"] == "第一问"
    assert overview[1]["message_count"] == 4


def test_clear_deletes_messages_by_foreign_key(db_path: Path, repo) -> None:
    """删除会话时，消息跟着走数据库的 ON DELETE CASCADE，不留在表里。"""
    repo.append_turn("u1", "会被清掉", "好的")

    assert repo.clear("u1") is True
    assert repo.messages("u1") is None
    assert repo.clear("u1") is False

    with sqlite3.connect(db_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0


def test_build_messages_puts_system_prompt_first(repo) -> None:
    repo.append_turn("u1", "问题", "回答")

    built = repo.build_messages("u1")

    assert built[0]["role"] == "system"
    assert [item["content"] for item in built[1:]] == ["问题", "回答"]
