"""会话管理接口：列表、消息记录、清空、404。"""

from __future__ import annotations


def test_list_and_messages(api) -> None:
    api.post("/chat", json={"session_id": "u1", "message": "第一句"})

    sessions = api.get("/sessions").json()["sessions"]
    assert sessions == ["u1"]

    body = api.get("/sessions/u1/messages").json()
    assert body["session_id"] == "u1"
    assert [m["role"] for m in body["messages"]] == ["user", "assistant"]
    assert body["messages"][0]["content"] == "第一句"
    assert body["messages"][1]["content"] == "你好，我是助手。"


def test_clear_session_removes_records(api) -> None:
    api.post("/chat", json={"session_id": "u1", "message": "会被清掉"})

    assert api.delete("/sessions/u1").json() == {"session_id": "u1", "deleted": True}
    assert api.get("/sessions").json()["sessions"] == []
    assert api.get("/sessions/u1/messages").status_code == 404


def test_unknown_session_returns_404(api) -> None:
    assert api.get("/sessions/nobody/messages").status_code == 404
    assert api.delete("/sessions/nobody").status_code == 404
