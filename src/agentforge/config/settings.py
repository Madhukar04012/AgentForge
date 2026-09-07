"""Environment-driven settings."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any


@dataclass(frozen=True)
class Settings:
    """Process-wide settings. Override via environment variables."""

    openai_api_key: str | None = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY"))
    anthropic_api_key: str | None = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY"))
    default_model: str = field(default_factory=lambda: os.environ.get("AGENTFORGE_MODEL", "gpt-4o-mini"))
    request_timeout: float = field(default_factory=lambda: float(os.environ.get("AGENTFORGE_TIMEOUT", "30")))
    extra: dict[str, Any] = field(default_factory=dict)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()