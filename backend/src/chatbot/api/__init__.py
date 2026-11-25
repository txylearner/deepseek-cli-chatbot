"""HTTP 接口层：只负责请求解析、依赖注入与响应返回。"""

from .router import router

__all__ = ["router"]
