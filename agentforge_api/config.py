# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Application settings, sourced from environment variables.

The :class:`Settings` model is loaded once via :func:`get_settings`. All
fields have safe defaults so a fresh checkout can boot without any
``AGENTFORGE_*`` environment variables; production deployments
override them in their environment.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process-wide configuration."""

    model_config = SettingsConfigDict(
        env_prefix="AGENTFORGE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- HTTP server -----------------------------------------------------
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False
    log_level: str = "info"

    # --- Database --------------------------------------------------------
    # Default to a local SQLite file so a fresh checkout boots without a
    # Postgres. Production overrides ``AGENTFORGE_DB_URL`` to a postgres
    # DSN.
    db_url: str = "sqlite:///./agentforge.db"
    db_echo: bool = False

    # --- Redis -----------------------------------------------------------
    # Used for the queue and pub/sub in later phases. Phase 1 only
    # configures the value.
    redis_url: str = "redis://localhost:6379/0"

    # --- Security --------------------------------------------------------
    jwt_secret: str = Field(default="dev-only-not-for-production", min_length=8)
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 30
    session_cookie_name: str = "agentforge_session"
    demo_cookie_name: str = "agentforge_demo"

    # --- Demo / Recruiter mode ------------------------------------------
    demo_mode: bool = True
    demo_session_ttl_minutes: int = 60
    demo_max_executions_per_session: int = 5

    # --- CORS ------------------------------------------------------------
    # Comma-separated string, parsed by :pyattr:`cors_origins_list`.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Misc ------------------------------------------------------------
    environment: str = "development"

    @property
    def cors_origins_list(self) -> List[str]:
        """Split ``cors_origins`` on commas and strip whitespace."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    The first call reads from the environment; subsequent calls return
    the cached value. Tests can clear the cache by calling
    :func:`_reset_settings_cache`.
    """
    return Settings()


def _reset_settings_cache() -> None:
    """Clear the LRU cache — useful for tests that mutate env vars."""
    get_settings.cache_clear()
