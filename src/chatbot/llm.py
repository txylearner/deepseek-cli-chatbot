"""DeepSeek chat completion wrapper.

DeepSeek exposes an OpenAI-compatible API, so the official OpenAI Python SDK
works with a custom base_url and model name.
"""

from __future__ import annotations

from collections.abc import Iterator

from openai import OpenAI

from .config import Settings


def build_client(settings: Settings) -> OpenAI:
    """Create an OpenAI-compatible client for DeepSeek."""
    return OpenAI(
        api_key=settings.api_key_value,
        base_url=settings.base_url,
    )


def stream_chat(
    messages: list[dict[str, str]],
    settings: Settings,
    client: OpenAI | None = None,
) -> Iterator[str]:
    """Yield text deltas from a streaming DeepSeek chat completion.

    The client parameter exists so tests can inject a fake client and run
    completely offline.
    """
    client = client or build_client(settings)
    stream = client.chat.completions.create(
        model=settings.model,
        messages=messages,
        temperature=settings.temperature,
        stream=True,
    )

    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

def complete_chat(
    messages: list[dict[str, str]],
    settings: Settings,
    client: OpenAI | None = None,
) -> str:
    """把流式片段拼成完整回复。

    /chat 这类一次性返回的接口用它；实现上仍然走 stream_chat，
    这样一次性接口和流式接口共用同一段模型调用逻辑。
    """
    return "".join(stream_chat(messages, settings, client=client))
