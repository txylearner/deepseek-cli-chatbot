"""会话仓库：会话与消息的唯一读写入口。

路由层和 Service 只依赖这里暴露的方法，不关心底层是内存、SQLite
还是 MySQL。换存储时只需要新增一个实现并替换注入。

当前实现是内存字典（重构阶段），下一步会替换为 SQLite。
"""

from __future__ import annotations

import threading
from typing import Protocol

from ..core.prompts import SYSTEM_PROMPT
from ..models.schemas import Message


class SessionRepository(Protocol):
    """仓库接口：描述“会话存储”必须提供的能力。"""

    def get_or_create(self, session_id: str) -> list[Message]: ...

    def exists(self, session_id: str) -> bool: ...

    def list_ids(self) -> list[str]: ...

    def messages(self, session_id: str) -> list[Message] | None: ...

    def add_message(self, session_id: str, role: str, content: str) -> None: ...

    def drop_last_message(self, session_id: str) -> None: ...

    def clear(self, session_id: str) -> bool: ...

    def reset(self) -> None: ...

    def build_messages(self, session_id: str) -> list[Message]: ...


class InMemorySessionRepository:
    """线程安全的内存实现，用于重构阶段和单元测试。"""

    def __init__(self) -> None:
        self._sessions: dict[str, list[Message]] = {}
        self._lock = threading.RLock()

    def get_or_create(self, session_id: str) -> list[Message]:
        with self._lock:
            return self._sessions.setdefault(session_id, [])

    def exists(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._sessions

    def list_ids(self) -> list[str]:
        with self._lock:
            return list(self._sessions)

    def messages(self, session_id: str) -> list[Message] | None:
        with self._lock:
            messages = self._sessions.get(session_id)
            if messages is None:
                return None
            return [dict(message) for message in messages]

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            self._sessions.setdefault(session_id, []).append(
                {"role": role, "content": content}
            )

    def drop_last_message(self, session_id: str) -> None:
        with self._lock:
            messages = self._sessions.get(session_id)
            if messages:
                messages.pop()

    def clear(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def reset(self) -> None:
        with self._lock:
            self._sessions.clear()

    def build_messages(self, session_id: str) -> list[Message]:
        with self._lock:
            history = [dict(message) for message in self._sessions.get(session_id, [])]
        return [{"role": "system", "content": SYSTEM_PROMPT}, *history]
