from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _resolve_sqlite(url: str) -> str:
    if not url.startswith("sqlite:///"):
        return url
    path = url.replace("sqlite:///", "", 1)
    if path.startswith("/") or path.startswith("////"):
        return url
    abs_path = (BASE_DIR / path).resolve()
    return f"sqlite:///{abs_path}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    secret_key: str = "nexus-dev-secret-change-in-production"
    debug: bool = True
    database_url: str = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    redis_url: str = "redis://localhost:6379/0"
    cors_allowed_origins: str = "http://localhost:3000,http://127.0.0.1:8000"

    binance_api_key: str = ""
    binance_secret: str = ""
    okx_api_key: str = ""
    okx_secret: str = ""
    okx_password: str = ""

    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    @model_validator(mode="after")
    def celery_defaults(self):
        object.__setattr__(self, "database_url", _resolve_sqlite(self.database_url))
        if not self.celery_broker_url:
            object.__setattr__(self, "celery_broker_url", self.redis_url)
        if not self.celery_result_backend:
            object.__setattr__(self, "celery_result_backend", self.redis_url)
        return self

    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
