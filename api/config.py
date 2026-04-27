"""
Application configuration — loaded once at startup via pydantic-settings.
Reads from environment variables and the .env file in the project root.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the .env file relative to the project root (parent of this api/ package)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_FILE = os.path.join(_PROJECT_ROOT, ".env")


class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str

    # CORS — comma-separated origins, or "*" for open
    cors_origins: str = "*"

    # Logging level
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once at startup)."""
    return Settings()
