"""应用配置：唯一读取环境变量和 .env 的地方。

所有可调参数都集中在 Settings 里，其他模块通过 get_settings() 取，
测试时用 cache_clear() 重新读取。
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """运行时配置，可被 CHATBOT_ 前缀的环境变量或 .env 覆盖。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CHATBOT_",
        extra="ignore",
        case_sensitive=False,
    )

    model: str = "deepseek-chat"
    base_url: str = "https://api.deepseek.com"
    api_key: SecretStr
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_history: int = Field(default=20, ge=1, le=100)
    db_path: str = "chat.db"

    @property
    def api_key_value(self) -> str:
        """只在创建客户端时取出明文，绝不用于日志或响应。"""
        return self.api_key.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    """返回唯一的 Settings 实例；测试里调用 cache_clear() 重置。"""
    return Settings()
