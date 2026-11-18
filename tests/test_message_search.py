"""关键词查询：全量、命中、顺序、跨会话隔离、通配符转义与 404。"""

from __future__ import annotations


def _seed(api) -> None:
    """u1 里放能搜到与搜不到的几条；u2 里放一条同关键词的，用来验证隔离。"""
    api.post("/chat", json={"session_id": "u1", "message": "SQLite 的索引怎么建"})
    api.post("/chat", json={"session_id": "u1", "message": "今天天气不错"})
    api.post("/chat", json={"session_id": "u1", "message": "索引能加速查询吗"})
    api.post("/chat", json={"session_id": "u2", "message": "SQLite 支持并发吗"})


def test_without_keyword_returns_full_history(api) -> None:
    _seed(api)

    body = api.get("/sessions/u1/messages").json()

    assert [item["content"] for item in body["messages"]] == [
        "SQLite 的索引怎么建",
        "你好，我是助手。",
        "今天天气不错",
        "你好，我是助手。",
        "索引能加速查询吗",
        "你好，我是助手。",
    ]


def test_keyword_returns_only_matching_messages(api) -> None:
    _seed(api)

    body = api.get("/sessions/u1/messages", params={"keyword": "SQLite"}).json()

    assert body["session_id"] == "u1"
    assert [item["content"] for item in body["messages"]] == ["SQLite 的索引怎么建"]


def test_keyword_keeps_the_original_order(api) -> None:
    _seed(api)

    body = api.get("/sessions/u1/messages", params={"keyword": "索引"}).json()

    assert [item["content"] for item in body["messages"]] == [
        "SQLite 的索引怎么建",
        "索引能加速查询吗",
    ]


def test_keyword_does_not_cross_sessions(api) -> None:
    _seed(api)

    mine = api.get("/sessions/u1/messages", params={"keyword": "并发"}).json()
    other = api.get("/sessions/u2/messages", params={"keyword": "并发"}).json()

    assert mine["messages"] == []
    assert [item["content"] for item in other["messages"]] == ["SQLite 支持并发吗"]


def test_no_match_returns_empty_list(api) -> None:
    _seed(api)

    response = api.get("/sessions/u1/messages", params={"keyword": "不存在的词"})

    assert response.status_code == 200
    assert response.json()["messages"] == []


def test_blank_keyword_means_full_history(api) -> None:
    _seed(api)
    full = api.get("/sessions/u1/messages").json()["messages"]

    for blank in ("", "   "):
        body = api.get("/sessions/u1/messages", params={"keyword": blank}).json()
        assert body["messages"] == full


def test_percent_is_a_literal_not_a_wildcard(api) -> None:
    """关键词里的 % 必须当普通字符，否则会误命中所有消息。"""
    api.post("/chat", json={"session_id": "u1", "message": "完成度 100% 了"})
    api.post("/chat", json={"session_id": "u1", "message": "完成度 100 了"})

    body = api.get("/sessions/u1/messages", params={"keyword": "100%"}).json()

    assert [item["content"] for item in body["messages"]] == ["完成度 100% 了"]


def test_unknown_session_still_returns_404(api) -> None:
    response = api.get("/sessions/nobody/messages", params={"keyword": "你好"})

    assert response.status_code == 404


def test_too_long_keyword_is_rejected(api) -> None:
    response = api.get("/sessions/u1/messages", params={"keyword": "x" * 101})

    assert response.status_code == 422
