"""学习功能：单词讲解。

只负责“怎么问模型”，不关心 HTTP 和会话存储，
这样测试时可以单独测这一段，也可以以后复用到别的接口。
"""

from __future__ import annotations

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
