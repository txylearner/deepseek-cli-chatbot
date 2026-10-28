"""Application settings loaded from environment variables and .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Every tunable value lives here. Values can be overridden by environment
    variables with the CHATBOT_ prefix, or by a local .env file.
    """

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

    @property
    def api_key_value(self) -> str:
        """Return the plaintext key for the API client only, never for logging."""
        return self.api_key.get_secret_value()


@lru_cache
def get_settings() -> Settings:
    """Return one cached Settings instance; tests can call cache_clear()."""
    return Settings()
