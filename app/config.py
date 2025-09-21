from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


def _env_bool(key: str, default: bool = False) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    """Application configuration derived from environment variables."""

    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./mock.db"))
    mock_token: str = field(default_factory=lambda: os.getenv("MOCK_TOKEN", "MOCK_SUPER_SECRET"))
    allow_reset: bool = field(default_factory=lambda: _env_bool("MOCK_ALLOW_RESET", False))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
