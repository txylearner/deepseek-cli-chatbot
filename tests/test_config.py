"""Offline tests for configuration parsing and secret handling."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from chatbot.config import get_settings

ENV_NAMES = (
    "CHATBOT_API_KEY",
    "CHATBOT_BASE_URL",
    "CHATBOT_MODEL",
    "CHATBOT_TEMPERATURE",
    "CHATBOT_MAX_HISTORY",
)


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch, tmp_path):
    """Keep tests away from the real .env file and the lru_cache."""
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_defaults_and_secret_masking(monkeypatch):
    monkeypatch.setenv("CHATBOT_API_KEY", "sk-test")

    settings = get_settings()

    assert settings.model == "deepseek-chat"
    assert settings.base_url == "https://api.deepseek.com"
    assert settings.temperature == 0.7
    assert settings.max_history == 20
    assert "sk-test" not in str(settings)
    assert "sk-test" not in repr(settings)
    assert settings.api_key.get_secret_value() == "sk-test"


def test_temperature_out_of_range_raises(monkeypatch):
    monkeypatch.setenv("CHATBOT_API_KEY", "sk-test")
    monkeypatch.setenv("CHATBOT_TEMPERATURE", "5")

    with pytest.raises(ValidationError):
        get_settings()
