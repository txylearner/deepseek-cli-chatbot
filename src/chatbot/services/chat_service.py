"""聊天业务：校验输入、记录消息、调用模型、回写回复。

路由层不碰仓库细节，也不碰模型参数；这些顺序约束都收在 Service 里，
所以 /chat 和 /chat/stream 不会出现两份不一样的业务逻辑。
"""

from __future__ import annotations

from collections.abc import Iterator

from openai import OpenAI

from ..core.config import Settings
from ..core.exceptions import EmptyFieldError, ModelCallError
from ..llm.deepseek import complete_chat, stream_chat
from ..repositories.session_repository import SessionRepository


class ChatService:
    def __init__(
        self,
        repository: SessionRepository,
        settings: Settings,
        client: OpenAI | None = None,
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._client = client

    @staticmethod
    def _clean(session_id: str, message: str) -> tuple[str, str]:
        session_id = session_id.strip()
        message = message.strip()
        if not session_id:
            raise EmptyFieldError("session_id 不能为空")
        if not message:
            raise EmptyFieldError("message 不能为空")
        return session_id, message

    def reply(self, session_id: str, message: str) -> str:
        """一次性回复：成功才把助手回复写进历史，失败回滚用户消息。"""
        session_id, message = self._clean(session_id, message)

        self._repository.get_or_create(session_id)
        self._repository.add_message(session_id, "user", message)
        try:
            answer = complete_chat(
                self._repository.build_messages(session_id),
                self._settings,
                client=self._client,
            )
        except Exception as exc:  # noqa: BLE001 - 统一转成 502，不泄露上游细节
            self._repository.drop_last_message(session_id)
            raise ModelCallError(f"模型调用失败：{type(exc).__name__}") from exc

        self._repository.add_message(session_id, "assistant", answer)
        return answer

    def stream(self, session_id: str, message: str) -> Iterator[str]:
        """流式回复：边产出边发送，结束时把已生成内容写回历史。"""
        session_id, message = self._clean(session_id, message)

        self._repository.get_or_create(session_id)
        self._repository.add_message(session_id, "user", message)
        messages = self._repository.build_messages(session_id)

        def generate() -> Iterator[str]:
            chunks: list[str] = []
            try:
                for delta in stream_chat(messages, self._settings, client=self._client):
                    chunks.append(delta)
                    yield delta
            finally:
                # 正常结束、报错、客户端断开都会走到这里
                if chunks:
                    self._repository.add_message(
                        session_id, "assistant", "".join(chunks)
                    )
                else:
                    self._repository.drop_last_message(session_id)

        return generate()
