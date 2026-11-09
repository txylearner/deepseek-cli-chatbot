"""所有提示词集中在这里。

提示词属于业务资产，只保存在服务端；前端拿不到，也不会出现在任何响应里。
"""

from __future__ import annotations

SYSTEM_PROMPT = "你是一个乐于助人的中文 AI 助手。回答要简洁、准确。"

STUDY_SYSTEM_PROMPT = (
    "你是一位耐心的英语老师。请用中文讲解用户给出的英语单词："
    "给出中文释义、词性和一个简短的英文例句，并附上例句的中文翻译。"
    "回答控制在 5 行以内。"
)


def build_word_messages(word: str) -> list[dict[str, str]]:
    """构造“单词讲解”的 messages。"""
    return [
        {"role": "system", "content": STUDY_SYSTEM_PROMPT},
        {"role": "user", "content": f"请讲解这个单词：{word}"},
    ]
