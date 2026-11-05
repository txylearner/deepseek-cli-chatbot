"""网页界面与静态资源的冒烟测试。

不测样式，只确认三件事：首页能打开、接口文档没被静态挂载挡住、
未知路径仍然返回 404。
"""

from __future__ import annotations


def test_index_page_is_served(api) -> None:
    response = api.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DeepSeek 对话助手" in response.text
    # 页面靠这两个接口工作，缺一个就没法聊天
    assert "/chat/stream" in response.text
    assert "/sessions" in response.text


def test_api_and_docs_still_reachable(api) -> None:
    assert api.get("/docs").status_code == 200
    assert api.get("/openapi.json").status_code == 200
    assert api.get("/health").json()["status"] == "ok"


def test_unknown_page_returns_404(api) -> None:
    assert api.get("/no-such-page").status_code == 404
