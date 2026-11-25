"""命令行版：与 Web 共用 Repository 和 ChatService。

第 2 次作业的交互式聊天保留下来，方便不启动服务时调试；
它和 Web 走的是同一套业务与存储代码，同样边收边打印。
"""

from __future__ import annotations

import sys

from pydantic import ValidationError

from ..core.config import get_settings
from ..repositories.session_repository import SQLiteSessionRepository
from ..services.chat_service import ChatService

SESSION_ID = "cli"


def _clean_line(text: str) -> str:
    """把终端里少数无法解码的字节替换掉，避免带着孤立代理字符进数据库。"""
    return text.encode("utf-8", errors="replace").decode("utf-8")


def _load_settings():
    """缺 Key 或配置不合法时给一句人话，而不是抛一整段 pydantic 堆栈。"""
    try:
        return get_settings()
    except ValidationError as exc:
        missing = [
            str(error["loc"][0]).upper()
            for error in exc.errors()
            if error.get("type") == "missing"
        ]
        if missing:
            names = "、".join("CHATBOT_" + name for name in missing)
            print(f"缺少配置：{names}")
            print("请把 .env.example 复制为 .env，填入 DeepSeek API Key 后重试。")
        else:
            print("配置不合法：" + str(exc.errors()[0].get("msg", "")))
        raise SystemExit(1)


def main() -> None:
    for stream in (sys.stdin, sys.stdout):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass

    settings = _load_settings()
    service = ChatService(SQLiteSessionRepository(settings.db_path), settings)
    print("DeepSeek 命令行聊天（输入 exit 退出）")

    while True:
        try:
            line = _clean_line(input("你 > ").strip())
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line in {"exit", "quit"}:
            break
        if not line:
            continue

        print("AI > ", end="", flush=True)
        try:
            for chunk in service.stream(SESSION_ID, line):
                print(chunk, end="", flush=True)
            print()
        except Exception as exc:  # noqa: BLE001 - 命令行只做友好提示
            print("\n出错：", exc)


if __name__ == "__main__":  # pragma: no cover
    main()
