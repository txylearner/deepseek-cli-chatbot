"""内存会话仓库。

本模块是唯一读写会话数据的地方：路由层只调用这里的函数，
以后要换成 Redis / 数据库时，只要替换本文件的实现即可。

数据结构：
    sessions = {
        "u1": [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，有什么可以帮你？"},
        ],
        ...
    }
"""

from __future__ import annotations

import threading

from .chat import SYSTEM_PROMPT

Message = dict[str, str]


class SessionStore:
    """线程安全的内存会话仓库，按 session_id 分组保存消息。"""

    def __init__(self) -> None:
        self._sessions: dict[str, list[Message]] = {}
        self._lock = threading.RLock()

    # ---------- 查询 ----------

    def get_or_create(self, session_id: str) -> list[Message]:
        """取出会话；第一次见到这个 ID 时创建空会话。"""
        with self._lock:
            return self._sessions.setdefault(session_id, [])

    def exists(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._sessions

    def list_ids(self) -> list[str]:
        """返回所有会话 ID，按创建顺序排列。"""
        with self._lock:
            return list(self._sessions)

    def messages(self, session_id: str) -> list[Message] | None:
        """返回会话的消息记录副本；会话不存在时返回 None。"""
        with self._lock:
            messages = self._sessions.get(session_id)
            if messages is None:
                return None
            return [dict(message) for message in messages]

    # ---------- 写入 ----------

    def add_message(self, session_id: str, role: str, content: str) -> None:
        with self._lock:
            self._sessions.setdefault(session_id, []).append(
                {"role": role, "content": content}
            )

    def drop_last_message(self, session_id: str) -> None:
        """删掉最后一条消息，用于模型调用失败时回滚刚加进去的 user 消息。"""
        with self._lock:
            messages = self._sessions.get(session_id)
            if messages:
                messages.pop()

    def clear(self, session_id: str) -> bool:
        """删除整个会话；返回是否真的存在过。"""
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def reset(self) -> None:
        """清空所有会话，测试之间用它隔离状态。"""
        with self._lock:
            self._sessions.clear()

    # ---------- 给模型用 ----------

    def build_messages(self, session_id: str) -> list[Message]:
        """拼出送给模型的消息列表：system prompt + 该会话的历史。"""
        with self._lock:
            history = [dict(message) for message in self._sessions.get(session_id, [])]
        return [{"role": "system", "content": SYSTEM_PROMPT}, *history]
