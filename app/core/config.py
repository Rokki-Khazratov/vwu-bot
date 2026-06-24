from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://vwu:vwu@localhost:5432/vwu"

    # Access
    allowlist_telegram_ids: Annotated[list[int], NoDecode] = []
    require_service_token: bool = False
    bot_service_token: str = ""
    dev_default_telegram_id: int | None = None

    # LLM (Gemini)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-pro"
    gemini_base_url: str = "https://generativelanguage.googleapis.com"

    @field_validator("allowlist_telegram_ids", mode="before")
    @classmethod
    def _parse_allowlist(cls, value: object) -> object:
        # Accept a comma-separated string from the environment.
        if isinstance(value, str):
            return [int(p) for p in value.split(",") if p.strip()]
        return value

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
