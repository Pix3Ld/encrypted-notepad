"""A module providing configuration variables."""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class AppConfig(BaseConfig):
    DB_HOST: Optional[str] = None
    DB_NAME: Optional[str] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None


def validate_db_config(cfg: AppConfig) -> None:
    missing = [
        name for name in ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
        if getattr(cfg, name) is None
    ]
    if missing:
        raise RuntimeError(f"Brak zmiennych DB: {', '.join(missing)}")


config = AppConfig()
validate_db_config(config)
