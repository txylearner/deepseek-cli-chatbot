"""系统接口：健康检查。"""

from __future__ import annotations

from fastapi import APIRouter

from .. import __version__

router = APIRouter(tags=["系统"])


@router.get("/health", summary="健康检查")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
