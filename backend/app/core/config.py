"""
Development Configuration for SQLite

Allows running Pensieve locally without Docker or PostgreSQL.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DevSettings(BaseSettings):
    """Development settings with SQLite instead of PostgreSQL."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Pensieve"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Database - SQLite for development
    database_url: str = "sqlite+aiosqlite:///./pensieve.db"

    # Security
    secret_key: str = "dev-secret-key-min-32-chars-for-development-only"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    password_min_length: int = 8

    # Encryption
    encryption_iterations: int = 100_000

    # ML Models - will be loaded on demand
    emotion_model_path: str = "./models/emotion"
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # Rate Limiting
    max_entries_per_day: int = 50
    max_reflections_per_week: int = 2

    # Confidence
    max_confidence_score: float = 0.80

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


@lru_cache
def get_settings() -> DevSettings:
    """Get cached settings instance."""
    return DevSettings()
