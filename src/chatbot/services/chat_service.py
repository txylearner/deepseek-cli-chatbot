"""聊天业务：校验输入、组装消息、调用模型、把一轮对话原子地写回。

路由层不碰仓库细节，也不碰模型参数；这些顺序约束都收在 Service 里，
所以 /chat 和 /chat/stream 不会出现两份不一样的业务逻辑。

事务边界：模型调用不能放进事务里——一次调用可能耗时数秒，而 SQLite 同一时刻
只允许一个写事务，长事务会让其他请求全部排队。所以这里先只读地取历史，
在内存里拼上本轮提问，等模型返回后再用一个事务把“提问 + 回复”一起写入。
"""

from __future__ import annotations

from collections.abc import Iterator

from openai import OpenAI

from ..core.config import Settings
from ..core.exceptions import EmptyFieldError, ModelCallError
from ..llm.deepseek import complete_chat, stream_chat
from ..repositories.session_repository import SessionRepository
from ..models.schemas import Message


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

    def _pending_messages(self, session_id: str, message: str) -> list[Message]:
        """发给模型的消息：系统提示 + 已存历史 + 本轮提问（还没落库）。"""
        return [
            *self._repository.build_messages(session_id),
            {"role": "user", "content": message},
        ]

    def reply(self, session_id: str, message: str) -> str:
        """一次性回复：模型成功返回后，提问与回复在同一事务里写入。"""
        session_id, message = self._clean(session_id, message)

        try:
            answer = complete_chat(
                self._pending_messages(session_id, message),
                self._settings,
                client=self._client,
            )
        except Exception as exc:  # noqa: BLE001 - 统一转成 502，不泄露上游细节
            raise ModelCallError(f"模型调用失败：{type(exc).__name__}") from exc

        self._repository.append_turn(session_id, message, answer)
        return answer

    def stream(self, session_id: str, message: str) -> Iterator[str]:
        """流式回复：边产出边发送，结束时把这一轮整体写回历史。"""
        session_id, message = self._clean(session_id, message)
        messages = self._pending_messages(session_id, message)

        def generate() -> Iterator[str]:
            chunks: list[str] = []
            try:
                for delta in stream_chat(messages, self._settings, client=self._client):
                    chunks.append(delta)
                    yield delta
            finally:
                # 正常结束、报错、客户端断开都会走到这里；
                # 一个字节都没生成时什么都不写，避免留下空的半轮对话
                if chunks:
                    self._repository.append_turn(
                        session_id, message, "".join(chunks)
                    )

        return generate()
