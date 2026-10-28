"""Command-line entry point."""

from __future__ import annotations

import sys

from pydantic import ValidationError

from .chat import ChatSession
from .config import get_settings
from .llm import stream_chat


def _format_config_error(exc: ValidationError) -> str:
    missing = {
        str(error.get("loc", ("?",))[0])
        for error in exc.errors()
        if error.get("type") == "missing"
    }
    if "api_key" in missing:
        return (
            "未配置 CHATBOT_API_KEY。\n"
            "请复制 .env.example 为 .env，并填入你的 DeepSeek API Key。"
        )
    return f"配置校验失败：{exc}"


def run() -> int:
    try:
        settings = get_settings()
    except ValidationError as exc:
        print(f"[配置错误] {_format_config_error(exc)}", file=sys.stderr)
        return 1

    session = ChatSession(max_history=settings.max_history)
    print("DeepSeek 命令行助手已启动。输入 exit 或 quit 退出。")
    print(f"当前模型：{settings.model}")

    while True:
        try:
            user_input = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            return 0

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("再见。")
            return 0

        session.add_user(user_input)
        session.trim_history()

        print("AI> ", end="", flush=True)
        chunks: list[str] = []
        try:
            for delta in stream_chat(session.build_messages(), settings):
                print(delta, end="", flush=True)
                chunks.append(delta)
        except KeyboardInterrupt:
            print("\n[已中断本轮生成]")
            if chunks:
                session.add_assistant("".join(chunks))
            else:
                session.remove_last_user()
            continue
        except Exception as exc:  # noqa: BLE001 - keep the CLI alive on API errors
            print(f"\n[调用失败] {type(exc).__name__}: {exc}", file=sys.stderr)
            if chunks:
                session.add_assistant("".join(chunks))
            else:
                session.remove_last_user()
            continue

        print()
        session.add_assistant("".join(chunks))


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
