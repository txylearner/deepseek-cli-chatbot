"""会话管理接口：列表、历史消息、清空。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..core.exceptions import SessionNotFoundError
from ..repositories.session_repository import SessionRepository
from .deps import get_repository

router = APIRouter(tags=["会话"])


@router.get("/sessions", summary="会话 ID 列表")
def list_sessions(
    repository: SessionRepository = Depends(get_repository),
) -> dict[str, list[str]]:
    return {"sessions": repository.list_ids()}


@router.get("/sessions/{session_id}/messages", summary="某会话的消息记录")
def list_messages(
    session_id: str,
    repository: SessionRepository = Depends(get_repository),
) -> dict[str, object]:
    messages = repository.messages(session_id)
    if messages is None:
        raise SessionNotFoundError(f"会话不存在：{session_id}")
    return {"session_id": session_id, "messages": messages}


@router.delete("/sessions/{session_id}", summary="清空会话")
def clear_session(
    session_id: str,
    repository: SessionRepository = Depends(get_repository),
) -> dict[str, object]:
    if not repository.clear(session_id):
        raise SessionNotFoundError(f"会话不存在：{session_id}")
    return {"session_id": session_id, "deleted": True}
