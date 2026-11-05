"""FastAPI 应用：把聊天机器人暴露成 HTTP 接口。

职责划分：
    store.py  负责“数据在哪”
    app.py    负责“HTTP 怎么进、怎么出”
    llm.py    负责“怎么和模型说话”
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .config import get_settings
from .llm import complete_chat, stream_chat
from .store import SessionStore
from .study import build_word_messages

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="DeepSeek 对话机器人 API",
    description="由命令行聊天机器人改造而来的 HTTP 服务。",
    version=__version__,
)

# 全局状态挂在 app.state 上：
#   store        —— 内存会话仓库
#   model_client —— 测试用的注入点，生产环境保持 None（由 settings 现建真实客户端）
app.state.store = SessionStore()
app.state.model_client = None


def get_store(request: Request) -> SessionStore:
    """依赖：取出当前应用的内存会话仓库。"""
    return request.app.state.store


def get_model_client(request: Request):
    """依赖：取出可注入的模型客户端；生产环境返回 None。"""
    return request.app.state.model_client


class ChatRequest(BaseModel):
    session_id: str = Field(description="由调用方提供的会话 ID")
    message: str = Field(description="用户这一轮说的话")


class ChatResponse(BaseModel):
    session_id: str
    reply: str


class WordRequest(BaseModel):
    word: str = Field(description="要讲解的英语单词")


class WordResponse(BaseModel):
    word: str
    explanation: str


@app.get("/health", summary="健康检查")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.post("/chat", response_model=ChatResponse, summary="一问一答")
def chat(
    payload: ChatRequest,
    store: SessionStore = Depends(get_store),
    client=Depends(get_model_client),
) -> ChatResponse:
    """接收一条消息，返回模型回复，并把这一轮写进会话历史。"""
    session_id = payload.session_id.strip()
    message = payload.message.strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id 不能为空")
    if not message:
        raise HTTPException(status_code=400, detail="message 不能为空")

    store.get_or_create(session_id)
    store.add_message(session_id, "user", message)
    try:
        reply = complete_chat(store.build_messages(session_id), get_settings(), client=client)
    except Exception as exc:  # noqa: BLE001 - 统一转成 502，避免把 Key 等细节抛给调用方
        store.drop_last_message(session_id)
        raise HTTPException(status_code=502, detail=f"模型调用失败：{type(exc).__name__}") from exc
    store.add_message(session_id, "assistant", reply)
    return ChatResponse(session_id=session_id, reply=reply)


@app.post("/chat/stream", summary="流式一问一答")
def chat_stream(
    payload: ChatRequest,
    store: SessionStore = Depends(get_store),
    client=Depends(get_model_client),
) -> StreamingResponse:
    """/chat 的流式版本：请求体相同，响应是逐块输出的纯文本。

    用 StreamingResponse 边收边发；生成器结束（正常或异常）时把已收到的
    内容写回历史，保证两个接口的会话记录一致。
    """
    session_id = payload.session_id.strip()
    message = payload.message.strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id 不能为空")
    if not message:
        raise HTTPException(status_code=400, detail="message 不能为空")

    store.get_or_create(session_id)
    store.add_message(session_id, "user", message)
    messages = store.build_messages(session_id)
    settings = get_settings()

    def generate() -> Iterator[str]:
        chunks: list[str] = []
        try:
            for delta in stream_chat(messages, settings, client=client):
                chunks.append(delta)
                yield delta
        finally:
            # 正常结束、报错、客户端断开都会走到这里，保证历史不丢
            if chunks:
                store.add_message(session_id, "assistant", "".join(chunks))
            else:
                store.drop_last_message(session_id)

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


@app.post("/study/word", response_model=WordResponse, summary="学习功能：单词讲解")
def explain_word(
    payload: WordRequest,
    client=Depends(get_model_client),
) -> WordResponse:
    """把单词交给一个“英语老师”提示词，返回中文讲解 + 例句。"""
    word = payload.word.strip()
    if not word:
        raise HTTPException(status_code=400, detail="word 不能为空")
    try:
        explanation = complete_chat(build_word_messages(word), get_settings(), client=client)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"模型调用失败：{type(exc).__name__}") from exc
    return WordResponse(word=word, explanation=explanation)


@app.get("/sessions", summary="会话 ID 列表")
def list_sessions(store: SessionStore = Depends(get_store)) -> dict[str, list[str]]:
    return {"sessions": store.list_ids()}


@app.get("/sessions/{session_id}/messages", summary="某会话的消息记录")
def list_messages(
    session_id: str, store: SessionStore = Depends(get_store)
) -> dict[str, object]:
    messages = store.messages(session_id)
    if messages is None:
        raise HTTPException(status_code=404, detail=f"会话不存在：{session_id}")
    return {"session_id": session_id, "messages": messages}


@app.delete("/sessions/{session_id}", summary="清空会话")
def clear_session(
    session_id: str, store: SessionStore = Depends(get_store)
) -> dict[str, object]:
    if not store.clear(session_id):
        raise HTTPException(status_code=404, detail=f"会话不存在：{session_id}")
    return {"session_id": session_id, "deleted": True}

# 挂载必须放在所有路由之后：/docs、/chat 等接口优先匹配，
# 没被接口占用的路径才会落到静态页面（"/" 返回聊天界面）。
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="web-ui")
