"""网页界面与静态资源：页面可访问、源码不下发、接口不被挡。"""

from __future__ import annotations


def test_index_page_is_served(api) -> None:
    response = api.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DeepSeek 对话助手" in response.text
    # 页面靠这几个接口工作，缺一个就没法聊天或显示会话
    assert "/chat/stream" in response.text
    assert "/sessions/overview" in response.text
    assert "SQLite" in response.text


def test_page_is_built_and_inlined(api) -> None:
    """浏览器拿到的是压缩后的单文件，不暴露 frontend/ 源码路径。"""
    response = api.get("/")

    assert "<style>" in response.text
    assert "<script>" in response.text
    assert "css/app.css" not in response.text
    assert "js/app.js" not in response.text
    assert "/*" not in response.text


def test_frontend_sources_are_not_served(api) -> None:
    assert api.get("/css/app.css").status_code == 404
    assert api.get("/js/app.js").status_code == 404


def test_page_does_not_leak_api_key(api) -> None:
    response = api.get("/")

    assert "sk-" not in response.text
    assert "API_KEY" not in response.text


def test_api_and_docs_still_reachable(api) -> None:
    assert api.get("/docs").status_code == 200
    assert api.get("/openapi.json").status_code == 200
    assert api.get("/health").json()["status"] == "ok"


def test_unknown_page_returns_404(api) -> None:
    assert api.get("/no-such-page").status_code == 404
