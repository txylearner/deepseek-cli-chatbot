"""应用装配：创建 FastAPI、注册路由与异常处理、挂载前端页面。

这个文件只做“组装”，不含业务逻辑：
    api/            路由
    services/       业务
    repositories/   存储
    llm/            模型调用
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api.router import router as api_router
from .core.exceptions import ChatbotError
from .repositories.session_repository import InMemorySessionRepository

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """启动时准备好的仓库；测试里会提前注入临时仓库。"""
    if app.state.repository is None:
        app.state.repository = InMemorySessionRepository()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="DeepSeek 对话机器人 API",
        description="分层架构的 HTTP 聊天服务，会话数据持久化到 SQLite。",
        version=__version__,
        lifespan=lifespan,
    )

    # 全局状态挂在 app.state：仓库与模型客户端都从这里注入
    application.state.repository = None
    application.state.model_client = None

    application.include_router(api_router)

    @application.exception_handler(ChatbotError)
    def handle_chatbot_error(request: Request, exc: ChatbotError) -> JSONResponse:
        """把领域异常统一翻译成 {"detail": ...}，状态码由异常自己决定。"""
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    # 挂载必须放在所有路由之后：接口优先匹配，剩下的才去找静态页面
    application.mount(
        "/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend"
    )
    return application


app = create_app()
