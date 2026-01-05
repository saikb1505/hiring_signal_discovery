"""Application configuration using Pydantic settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application settings
    app_name: str = "Job Search Query Formatter API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # OpenAI settings
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.3
    openai_max_tokens: int = 500
    openai_timeout: int = 30

    # SerperAPI settings
    serper_api_key: str
    serper_timeout: int = 30
    serper_max_results: int = 10

    # CORS settings
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    # Rate limiting (requests per minute)
    rate_limit_per_minute: int = 60

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or text

    # Database settings
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hsd"
    database_echo: bool = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Using lru_cache ensures settings are only loaded once.
    """
    return Settings()
