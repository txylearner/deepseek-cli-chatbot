"""命令行版：与 Web 共用 Repository 和 ChatService。

第 2 次作业的交互式聊天保留下来，方便不启动服务时调试；
它和 Web 走的是同一套业务与存储代码。
"""

from __future__ import annotations

from ..core.config import get_settings
from ..repositories.session_repository import InMemorySessionRepository
from ..services.chat_service import ChatService

SESSION_ID = "cli"


def main() -> None:
    service = ChatService(InMemorySessionRepository(), get_settings())
    print("DeepSeek 命令行聊天（输入 exit 退出）")
    while True:
        try:
            line = input("你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line in {"exit", "quit"}:
            break
        if not line:
            continue
        try:
            print("AI >", service.reply(SESSION_ID, line))
        except Exception as exc:  # noqa: BLE001 - 命令行只做友好提示
            print("出错：", exc)


if __name__ == "__main__":  # pragma: no cover
    main()
