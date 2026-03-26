"""Application settings and environment configuration."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'Contacts API'
    db_url: str = 'postgresql+psycopg2://postgres:postgres@localhost:5437/contacts_db'
    secret_key: str = 'change-me'
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 30
    verify_token_expire_minutes: int = 60 * 24
    reset_token_expire_minutes: int = 30

    redis_host: str = 'redis'
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str | None = None
    redis_user_cache_ttl: int = 300

    mail_from: str = 'noreply@example.com'
    mail_server: str = 'mailpit'
    mail_port: int = 1025
    frontend_base_url: str = 'http://127.0.0.1:8000'

    cloudinary_cloud_name: str = ''
    cloudinary_api_key: str = ''
    cloudinary_api_secret: str = ''

    cors_origins: List[str] = Field(default_factory=lambda: ['*'])


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance for dependency injection."""

    return Settings()
