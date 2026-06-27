from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = ""
    backend_base_url: str = "http://localhost:8000"
    bot_service_token: str = ""
    request_timeout_seconds: float = 60.0

    # Async evaluation polling (backend may return 202).
    eval_poll_timeout_seconds: float = 120.0
    eval_poll_interval_seconds: float = 2.0

    use_webhook: bool = False
    webhook_url: str = ""
    webhook_secret: str = ""
    redis_url: str = ""
    log_level: str = "INFO"

    @property
    def api_base(self) -> str:
        return self.backend_base_url.rstrip("/") + "/api/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
