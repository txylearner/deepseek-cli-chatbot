"""领域异常：Service 抛出语义化错误，应用层统一翻译成 HTTP 响应。

这样路由里不需要写 try/except，也不会把第三方错误的细节泄露给调用方。
"""

from __future__ import annotations


class ChatbotError(Exception):
    """所有业务异常的基类，status_code 决定返回给客户端的 HTTP 状态码。"""

    status_code = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EmptyFieldError(ChatbotError):
    """必填字段为空，属于调用方的请求错误。"""

    status_code = 400


class SessionNotFoundError(ChatbotError):
    """会话不存在。"""

    status_code = 404


class ModelCallError(ChatbotError):
    """上游模型调用失败。"""

    status_code = 502
