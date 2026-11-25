"""会话概览接口：消息条数、首条用户消息、最近更新时间与排序。"""

from __future__ import annotations


def test_overview_is_empty_without_sessions(api) -> None:
    assert api.get("/sessions/overview").json() == {"sessions": []}


def test_overview_returns_count_and_title(api) -> None:
    api.post("/chat", json={"session_id": "u1", "message": "第一段对话"})
    api.post("/chat", json={"session_id": "u1", "message": "第二段对话"})

    body = api.get("/sessions/overview").json()
    assert len(body["sessions"]) == 1

    item = body["sessions"][0]
    assert item["id"] == "u1"
    assert item["title"] == "第一段对话"
    assert item["message_count"] == 4
    assert item["updated_at"]


def test_overview_lists_recent_session_first(api) -> None:
    api.post("/chat", json={"session_id": "u1", "message": "先聊的"})
    api.post("/chat", json={"session_id": "u2", "message": "后聊的"})

    ids = [item["id"] for item in api.get("/sessions/overview").json()["sessions"]]

    assert ids == ["u2", "u1"]
