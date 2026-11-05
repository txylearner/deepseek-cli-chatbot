"""测试共用工具：假模型客户端 + 干净的会话状态。

所有测试都通过这里拿到“假模型”，因此不联网、不需要真实 API Key。
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from chatbot.app import app
from chatbot.config import get_settings

DEFAULT_CHUNKS = ("你好", "，我是助手。")


class FakeCompletions:
    """模仿 client.chat.completions：记录收到的参数，返回固定片段。"""

    def __init__(self, chunks: tuple[str, ...] = DEFAULT_CHUNKS) -> None:
        self.chunks = chunks
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return iter(
            [
                SimpleNamespace(
                    choices=[SimpleNamespace(delta=SimpleNamespace(content=chunk))]
                )
                for chunk in self.chunks
            ]
        )

    @property
    def last_call(self) -> dict:
        assert self.calls, "模型一次都没有被调用"
        return self.calls[-1]


class FakeClient:
    """模仿 OpenAI 客户端，只暴露 chat.completions.create。"""

    def __init__(self, chunks: tuple[str, ...] = DEFAULT_CHUNKS) -> None:
        self.completions = FakeCompletions(chunks)
        self.chat = SimpleNamespace(completions=self.completions)


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch, tmp_path):
    """用假 Key + 临时目录，避免读到真实的 .env。"""
    monkeypatch.setenv("CHATBOT_API_KEY", "sk-test")
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def fake_client() -> FakeClient:
    return FakeClient()


@pytest.fixture
def api(fake_client):
    """带上假模型的 TestClient，每条用例前后都清空会话。"""
    app.state.store.reset()
    app.state.model_client = fake_client
    with TestClient(app) as client:
        yield client
    app.state.model_client = None
    app.state.store.reset()
