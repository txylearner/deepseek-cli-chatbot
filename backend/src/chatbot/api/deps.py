"""路由依赖：把仓库、模型客户端、Service 组装好交给路由。

依赖集中在这里，测试时只要替换 app.state 里的对象，
路由和业务代码一行都不用改。
"""

from __future__ import annotations

from fastapi import Depends, Request

from ..core.config import get_settings
from ..repositories.session_repository import SessionRepository
from ..services.chat_service import ChatService
from ..services.study_service import StudyService


def get_repository(request: Request) -> SessionRepository:
    """取出当前应用的会话仓库（由 lifespan 初始化）。"""
    repository = request.app.state.repository
    if repository is None:  # pragma: no cover - 正常启动不会发生
        raise RuntimeError("会话仓库尚未初始化")
    return repository


def get_model_client(request: Request):
    """取出可注入的模型客户端；生产环境是 None，由 llm 模块现建。"""
    return request.app.state.model_client


def get_chat_service(
    repository: SessionRepository = Depends(get_repository),
    client=Depends(get_model_client),
) -> ChatService:
    return ChatService(repository, get_settings(), client=client)


def get_study_service(client=Depends(get_model_client)) -> StudyService:
    return StudyService(get_settings(), client=client)
