"""DeepSeek 调用封装。

DeepSeek 提供 OpenAI 兼容接口，所以仍然用 openai 官方 SDK，
只改 base_url 和 model。所有模型调用都从这里出去，方便替换与测试。
"""

from __future__ import annotations

from collections.abc import Iterator

from openai import OpenAI

from ..core.config import Settings


def build_client(settings: Settings) -> OpenAI:
    """创建指向 DeepSeek 的 OpenAI 兼容客户端。"""
    return OpenAI(
        api_key=settings.api_key_value,
        base_url=settings.base_url,
    )


def stream_chat(
    messages: list[dict[str, str]],
    settings: Settings,
    client: OpenAI | None = None,
) -> Iterator[str]:
    """逐块产出模型回复；client 参数用于测试注入假客户端。"""
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
    """把流式片段拼成完整回复，供 /chat 这类一次性接口使用。"""
    return "".join(stream_chat(messages, settings, client=client))
