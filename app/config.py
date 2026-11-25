"""Application settings loaded from environment variables (see .env.example)."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Values come from the environment or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-2.5-flash"
    allowed_origins: str = "http://localhost:8000"
    cache_ttl_seconds: int = Field(default=600, ge=0, le=86_400)
    rate_limit_plan: str = "10/minute"
    rate_limit_chat: str = "20/minute"
    log_level: str = "INFO"
    enable_docs: bool = True

    @property
    def has_gemini_key(self) -> bool:
        """Return True when a non-empty Gemini API key is configured."""
        return bool(self.gemini_api_key and self.gemini_api_key.get_secret_value().strip())

    @property
    def allowed_origin_list(self) -> list[str]:
        """Return the CORS allow-list as a list of origins."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings instance."""
    return Settings()
