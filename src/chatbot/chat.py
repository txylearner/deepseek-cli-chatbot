"""Conversation state and history management."""

from __future__ import annotations

SYSTEM_PROMPT = "你是一个乐于助人的中文 AI 助手。回答要简洁、准确。"


class ChatSession:
    """Keep the message history for one command-line session."""

    def __init__(self, max_history: int = 20) -> None:
        if max_history < 1:
            raise ValueError("max_history must be at least 1")
        self.max_history = max_history
        self.messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def remove_last_user(self) -> None:
        """Drop the pending user message after a failed request."""
        if len(self.messages) > 1 and self.messages[-1]["role"] == "user":
            self.messages.pop()

    def trim_history(self) -> None:
        """Keep the system prompt plus roughly the latest N turns.

        The system prompt is never removed. If trimming starts in the middle
        of a turn, leading assistant messages are dropped so the remaining
        history starts with a user message.
        """
        limit = self.max_history * 2
        if len(self.messages) <= 1 + limit:
            return

        body = self.messages[1:][-limit:]
        while body and body[0]["role"] != "user":
            body.pop(0)
        self.messages = [self.messages[0]] + body

    def build_messages(self) -> list[dict[str, str]]:
        """Return a copy of the history to send to the model."""
        return [dict(message) for message in self.messages]
