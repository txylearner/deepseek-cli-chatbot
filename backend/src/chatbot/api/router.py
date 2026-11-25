"""把各业务模块的路由汇总成一个总路由。"""

from __future__ import annotations

from fastapi import APIRouter

from . import chat, sessions, study, system

router = APIRouter()
router.include_router(system.router)
router.include_router(chat.router)
router.include_router(sessions.router)
router.include_router(study.router)
