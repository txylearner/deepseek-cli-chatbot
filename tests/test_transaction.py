"""事务边界：一轮对话要么两条消息都落库，要么一条都不留。

两种失败都要覆盖：数据库写入失败（模拟磁盘错误）与模型调用失败。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from chatbot.core.exceptions import StorageError
from chatbot.repositories.session_repository import SQLiteSessionRepository


class FailingRepository(SQLiteSessionRepository):
    """写助手回复时抛错，用来模拟“第二条 INSERT 失败”。"""

    def _insert_message(self, session, session_id, role, content, created_at):
        if role == "assistant":
            raise RuntimeError("写入助手回复失败")
        super()._insert_message(session, session_id, role, content, created_at)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "chat.db"


def _count(db_path: Path, table: str) -> int:
    with sqlite3.connect(db_path) as connection:
        return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_one_turn_writes_two_rows(db_path: Path) -> None:
    repo = SQLiteSessionRepository(db_path)

    repo.append_turn("u1", "问题", "回答")

    assert [item["role"] for item in repo.messages("u1")] == ["user", "assistant"]
    assert _count(db_path, "messages") == 2


def test_failed_write_leaves_no_half_turn(db_path: Path) -> None:
    """助手回复写不进去时，用户的提问也必须回滚，会话都不留下。"""
    repo = FailingRepository(db_path)

    with pytest.raises(RuntimeError):
        repo.append_turn("u1", "问题", "回答")

    assert repo.messages("u1") is None
    assert repo.list_ids() == []
    assert _count(db_path, "messages") == 0
    assert _count(db_path, "sessions") == 0


def test_api_write_failure_returns_500_without_half_turn(api, monkeypatch) -> None:
    def boom(*args, **kwargs):
        raise StorageError("写入失败")

    monkeypatch.setattr(SQLiteSessionRepository, "append_turn", boom)

    response = api.post("/chat", json={"session_id": "u1", "message": "你好"})

    assert response.status_code == 500
    assert api.get("/sessions").json()["sessions"] == []
    assert api.get("/sessions/u1/messages").status_code == 404


def test_model_failure_writes_nothing(api, fake_client, monkeypatch) -> None:
    """模型调用失败时整轮都不落库，不会只剩用户那一句。"""

    def boom(**kwargs):
        raise RuntimeError("上游超时")

    monkeypatch.setattr(fake_client.completions, "create", boom)

    response = api.post("/chat", json={"session_id": "u1", "message": "你好"})

    assert response.status_code == 502
    assert api.get("/sessions").json()["sessions"] == []
