"""学习功能：单词讲解。只负责编排提示词与模型调用。"""

from __future__ import annotations

from openai import OpenAI

from ..core.config import Settings
from ..core.exceptions import EmptyFieldError, ModelCallError
from ..core.prompts import build_word_messages
from ..llm.deepseek import complete_chat


class StudyService:
    def __init__(self, settings: Settings, client: OpenAI | None = None) -> None:
        self._settings = settings
        self._client = client

    def explain(self, word: str) -> str:
        word = word.strip()
        if not word:
            raise EmptyFieldError("word 不能为空")
        try:
            return complete_chat(
                build_word_messages(word), self._settings, client=self._client
            )
        except Exception as exc:  # noqa: BLE001
            raise ModelCallError(f"模型调用失败：{type(exc).__name__}") from exc
