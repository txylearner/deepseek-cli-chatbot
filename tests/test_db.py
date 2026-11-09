"""数据库层测试：建表、历史连续、会话隔离、清空、重启后仍然存在。

全部使用 pytest 的 tmp_path 临时数据库，不读写开发者本地的 .env 和 chat.db。
"""

from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from chatbot.app import app, create_app
from chatbot.core.config import get_settings
from chatbot.repositories.session_repository import SQLiteSessionRepository


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "chat.db"


@pytest.fixture
def repo(db_path):
    return SQLiteSessionRepository(db_path)


def _table_names(path) -> set[str]:
    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    return {row[0] for row in rows}


def test_schema_is_created(db_path, repo) -> None:
    """建表成功：两张表、消息表外键指向会话表、查询索引都在。"""
    assert {"sessions", "messages"} <= _table_names(db_path)

    with sqlite3.connect(db_path) as connection:
        foreign_keys = connection.execute("PRAGMA foreign_key_list(messages)").fetchall()
        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }

    assert any(row[2] == "sessions" and row[3] == "session_id" for row in foreign_keys)
    assert "idx_messages_session" in indexes


def test_history_is_continuous_in_one_session(repo) -> None:
    """同一会话的历史按写入顺序连续取出，system 提示词永远在最前面。"""
    repo.add_message("u1", "user", "我叫小明")
    repo.add_message("u1", "assistant", "你好，小明")
    repo.add_message("u1", "user", "我叫什么")

    assert repo.messages("u1") == [
        {"role": "user", "content": "我叫小明"},
        {"role": "assistant", "content": "你好，小明"},
        {"role": "user", "content": "我叫什么"},
    ]

    built = repo.build_messages("u1")
    assert built[0]["role"] == "system"
    assert [message["content"] for message in built[1:]] == [
        "我叫小明",
        "你好，小明",
        "我叫什么",
    ]


def test_sessions_do_not_mix(repo) -> None:
    """两个会话的数据互不干扰。"""
    repo.add_message("u1", "user", "我是小明")
    repo.add_message("u2", "user", "我是小红")

    assert repo.messages("u1") == [{"role": "user", "content": "我是小明"}]
    assert repo.messages("u2") == [{"role": "user", "content": "我是小红"}]
    assert all("小明" not in message["content"] for message in repo.build_messages("u2"))


def test_clear_removes_session_and_messages(db_path, repo) -> None:
    """清空会话后，会话和它的消息一起消失（外键级联删除）。"""
    repo.add_message("u1", "user", "会被清掉")

    assert repo.clear("u1") is True
    assert repo.messages("u1") is None
    assert repo.list_ids() == []

    with sqlite3.connect(db_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0

    assert repo.clear("u1") is False


def test_reopen_keeps_data(db_path) -> None:
    """换一个新仓库对象（等价于服务重启）后，数据仍然在。"""
    first = SQLiteSessionRepository(db_path)
    first.add_message("u1", "user", "重启前的问题")
    first.add_message("u1", "assistant", "重启前的回答")

    second = SQLiteSessionRepository(db_path)

    assert second.list_ids() == ["u1"]
    assert second.messages("u1") == [
        {"role": "user", "content": "重启前的问题"},
        {"role": "assistant", "content": "重启前的回答"},
    ]


def test_drop_last_message_rolls_back(repo) -> None:
    """模型调用失败时回滚最后一条提问。"""
    repo.add_message("u1", "user", "失败的一问")

    repo.drop_last_message("u1")

    assert repo.messages("u1") == []


def test_reset_clears_everything(repo) -> None:
    repo.add_message("u1", "user", "a")
    repo.add_message("u2", "user", "b")

    repo.reset()

    assert repo.list_ids() == []
    assert repo.messages("u1") is None


def test_api_keeps_history_after_restart(tmp_path, fake_client) -> None:
    """通过 API 写入后重建仓库，仍能查到与重启前一致的记录。"""
    db_file = tmp_path / "chat.db"
    app.state.repository = SQLiteSessionRepository(db_file)
    app.state.model_client = fake_client
    try:
        with TestClient(app) as client:
            response = client.post(
                "/chat", json={"session_id": "u1", "message": "重启前说的话"}
            )
            assert response.status_code == 200

        app.state.repository = SQLiteSessionRepository(db_file)
        with TestClient(app) as client:
            body = client.get("/sessions/u1/messages").json()

        assert [message["role"] for message in body["messages"]] == [
            "user",
            "assistant",
        ]
        assert body["messages"][0]["content"] == "重启前说的话"
    finally:
        app.state.repository = None
        app.state.model_client = None


def test_startup_creates_database_file(tmp_path, monkeypatch) -> None:
    """不注入仓库时，服务启动会按配置自动建库建表。"""
    target = tmp_path / "auto.db"
    monkeypatch.setenv("CHATBOT_DB_PATH", str(target))
    get_settings.cache_clear()

    fresh_app = create_app()
    with TestClient(fresh_app) as client:
        assert client.get("/health").status_code == 200

    assert target.exists()
    get_settings.cache_clear()
