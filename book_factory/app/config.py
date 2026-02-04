"""Configuration for KDP Book Factory."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "KDP Book Factory"
    debug: bool = False

    database_path: str = str(DATA_DIR / "kdpfactory.db")
    storage_path: str = str(DATA_DIR / "topics")

    # Redis (optional if you add RQ later)
    redis_url: str = "redis://localhost:6379/0"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_timeout: int = 120

    # Anthropic (writer/rewriter)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Eve Integration
    eve_webhook_url: str = ""
    eve_api_key: str = ""
    eve_enabled: bool = True

    # Voice/TTS
    tts_provider: str = "edge"  # edge|elevenlabs
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # Trend monitoring (RSS-based, captcha-free)
    trend_rss_feeds: List[str] = Field(default_factory=list)
    trend_poll_interval_seconds: int = 1800

    # X API (OAuth 1.0a)
    x_consumer_key: str = ""
    x_consumer_secret: str = ""
    x_access_token: str = ""
    x_access_token_secret: str = ""
    x_min_seconds_between_calls: float = 2.0
    x_max_calls_per_run: int = 50

    # Targets
    draft_target_words_default: int = 25000
    final_target_words_default: int = 30000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @field_validator("trend_rss_feeds", mode="before")
    @classmethod
    def _split_feeds(cls, value):
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            return items
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
