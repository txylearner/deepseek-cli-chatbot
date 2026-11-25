"""POST /chat 的行为：连续对话、会话隔离、学习功能、参数校验。"""

from __future__ import annotations

from chatbot import __version__


def test_same_session_keeps_history(api, fake_client) -> None:
    first = api.post("/chat", json={"session_id": "u1", "message": "我叫小明"})
    assert first.status_code == 200
    assert first.json() == {"session_id": "u1", "reply": "你好，我是助手。"}

    second = api.post("/chat", json={"session_id": "u1", "message": "我叫什么"})
    assert second.status_code == 200

    sent = fake_client.completions.last_call["messages"]
    assert [m["role"] for m in sent] == ["system", "user", "assistant", "user"]
    assert sent[1]["content"] == "我叫小明"
    assert sent[-1]["content"] == "我叫什么"


def test_sessions_do_not_mix(api, fake_client) -> None:
    api.post("/chat", json={"session_id": "u1", "message": "我是小明"})
    api.post("/chat", json={"session_id": "u2", "message": "我是小红"})

    sent = fake_client.completions.last_call["messages"]
    user_contents = [m["content"] for m in sent if m["role"] == "user"]
    assert user_contents == ["我是小红"]
    assert all("小明" not in m["content"] for m in sent)


def test_study_feature_is_callable_over_http(api, fake_client) -> None:
    response = api.post("/study/word", json={"word": "apple"})

    assert response.status_code == 200
    body = response.json()
    assert body["word"] == "apple"
    assert body["explanation"] == "你好，我是助手。"
    system_prompt = fake_client.completions.last_call["messages"][0]["content"]
    assert "英语" in system_prompt


def test_empty_message_is_rejected(api) -> None:
    response = api.post("/chat", json={"session_id": "u1", "message": "   "})

    assert response.status_code == 400
    assert api.get("/sessions").json()["sessions"] == []


def test_response_never_leaks_api_key(api) -> None:
    response = api.post("/chat", json={"session_id": "u1", "message": "hi"})

    assert "sk-test" not in response.text
    assert response.json()["reply"] == "你好，我是助手。"
    assert __version__ in api.get("/health").json()["version"]
