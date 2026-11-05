"""POST /chat/stream：确认真的开了 stream=True，且内容会写回历史。"""

from __future__ import annotations


def test_stream_passes_stream_true(api, fake_client) -> None:
    with api.stream(
        "POST", "/chat/stream", json={"session_id": "u1", "message": "讲个笑话"}
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        body = "".join(response.iter_text())

    assert body == "你好，我是助手。"
    assert fake_client.completions.last_call["stream"] is True


def test_stream_reply_is_saved_to_history(api) -> None:
    api.post("/chat/stream", json={"session_id": "s1", "message": "第一句"})

    messages = api.get("/sessions/s1/messages").json()["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "第一句"
    assert messages[1]["content"] == "你好，我是助手。"
