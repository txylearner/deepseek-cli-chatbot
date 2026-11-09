"""API 数据模型与消息结构。

Pydantic 模型负责请求体校验与响应序列化；
Message 是仓库与模型之间传递的统一消息形状。
"""

from __future__ import annotations

from pydantic import BaseModel, Field

Message = dict[str, str]


class ChatRequest(BaseModel):
    session_id: str = Field(description="由调用方提供的会话 ID")
    message: str = Field(description="用户这一轮说的话")


class ChatResponse(BaseModel):
    session_id: str
    reply: str


class SessionOverview(BaseModel):
    id: str
    title: str = ""
    message_count: int = 0
    updated_at: str


class SessionOverviewResponse(BaseModel):
    sessions: list[SessionOverview]


class WordRequest(BaseModel):
    word: str = Field(description="要讲解的英语单词")


class WordResponse(BaseModel):
    word: str
    explanation: str
