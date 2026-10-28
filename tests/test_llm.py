"""Offline test for the parameters sent to the model."""

from __future__ import annotations

from types import SimpleNamespace

from chatbot.config import Settings
from chatbot.llm import stream_chat


class FakeCompletions:
    def __init__(self) -> None:
        self.kwargs: dict | None = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return iter(
            [
                SimpleNamespace(
                    choices=[SimpleNamespace(delta=SimpleNamespace(content="你"))]
                ),
                SimpleNamespace(
                    choices=[SimpleNamespace(delta=SimpleNamespace(content="好"))]
                ),
                SimpleNamespace(choices=[]),
            ]
        )


class FakeClient:
    def __init__(self) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions())


def _settings() -> Settings:
    return Settings(api_key="sk-test", _env_file=None)


def test_stream_chat_passes_expected_parameters() -> None:
    client = FakeClient()
    messages = [
        {"role": "system", "content": "你是一个助手。"},
        {"role": "user", "content": "你好"},
    ]

    chunks = list(stream_chat(messages, _settings(), client=client))

    assert chunks == ["你", "好"]

    kwargs = client.chat.completions.kwargs
    assert kwargs is not None
    assert kwargs["model"] == "deepseek-chat"
    assert kwargs["temperature"] == 0.7
    assert kwargs["messages"] == messages
    assert kwargs["stream"] is True
    assert [message["role"] for message in kwargs["messages"]] == [
        "system",
        "user",
    ]
