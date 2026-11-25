"""对话接口：一次性回复与流式回复。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from ..models.schemas import ChatRequest, ChatResponse
from ..services.chat_service import ChatService
from .deps import get_chat_service

router = APIRouter(tags=["对话"])


@router.post("/chat", response_model=ChatResponse, summary="一问一答")
def chat(
    payload: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    reply = service.reply(payload.session_id, payload.message)
    return ChatResponse(session_id=payload.session_id.strip(), reply=reply)


@router.post("/chat/stream", summary="流式一问一答")
def chat_stream(
    payload: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    stream = service.stream(payload.session_id, payload.message)
    return StreamingResponse(stream, media_type="text/plain; charset=utf-8")
