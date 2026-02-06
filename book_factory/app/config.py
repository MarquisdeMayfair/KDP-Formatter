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

    # OpenAI-compatible (GPT, Grok, etc.)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com"
    openai_model: str = "gpt-4.1"
    openai_compat_path: str = "/v1/chat/completions"

    # Grok (xAI) OpenAI-compatible endpoint
    grok_api_key: str = ""
    grok_base_url: str = "https://api.x.ai"
    grok_model: str = "grok-2-latest"

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
    x_bearer_token: str = ""

    # GitHub
    github_token: str | None = None

    # Google CSE
    google_cse_api_key: str | None = None
    google_cse_cx: str = "3767d9260c5464710"
    google_cse_date_restrict: str = "d30"
    google_cse_results_per_query: int = 3
    cse_primary_domains: List[str] = Field(
        default_factory=lambda: [
            "substack.com",
            "medium.com",
            "theverge.com",
            "wired.com",
            "techcrunch.com",
            "techradar.com",
        ]
    )

    # RSSHub (optional for Substack discovery)
    rsshub_base_url: str = ""

    # Targets
    draft_target_words_default: int = 25000
    final_target_words_default: int = 30000

    # Ingestion quality gate
    ingest_min_words: int = 300

    # Draft caps (to avoid budget blowouts)
    draft_max_words_per_silo: int = 5000
    draft_max_words_total: int = 30000

    # Swarm / ghostwriter settings
    swarm_writer_provider: str = "anthropic"  # anthropic|openai|grok|ollama
    swarm_research_provider: str = "grok"  # grok|openai|anthropic|ollama|none
    swarm_max_parallel: int = 3
    swarm_use_x: bool = True
    swarm_include_unassigned_ideas: bool = True
    swarm_use_web: bool = True
    swarm_web_sources_per_chapter: int = 2
    swarm_web_max_words: int = 300

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

    @field_validator("cse_primary_domains", mode="before")
    @classmethod
    def _split_domains(cls, value):
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            return items
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
