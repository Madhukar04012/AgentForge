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

"""FastAPI application factory for the AgentForge web platform.

The factory wires up settings, middleware, exception handlers, the
``api_v1_router``, and an OpenAPI schema. CORS origins come from
``Settings.cors_origins``; a request-ID middleware decorates every
request with an ``X-Request-ID`` header; a demo-mode middleware
attaches ``X-Demo-Mode: 1`` when the request was issued by an
anonymous demo session.

This module is intentionally small. Business logic lives in
``routers/`` and ``services/`` (introduced in later phases).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .config import get_settings
from .middleware import DemoModeMiddleware, RequestIDMiddleware
from .routers import api_v1_router


def create_app() -> FastAPI:
    """Create and return a configured FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="AgentForge API",
        version=__version__,
        description=(
            "HTTP API for the AgentForge web platform. Phase 1 ships "
            "skeleton endpoints only; real domain endpoints arrive in "
            "Phase 2+."
        ),
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS — strict allowlist per environment.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "X-Demo-Mode"],
        max_age=600,
    )

    # Custom middleware — request-id and demo-mode banner.
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(DemoModeMiddleware, enabled=settings.demo_mode)

    # Routers.
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


# Module-level app for ``uvicorn agentforge_api.app:app``.
app = create_app()
