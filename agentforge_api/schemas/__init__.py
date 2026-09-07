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

"""Pydantic request/response schemas.

Phase 1 shipped the schemas the Phase 1 endpoints need:
  * :class:`HealthOut` — liveness probe.
  * :class:`LoginIn` / :class:`TokenOut` — placeholder auth.
  * :class:`UserOut` — current user.
  * :class:`DemoSessionOut` / :class:`DemoProjectOut` — recruiter demo.

Phase 2 adds:
  * :mod:`agentforge_api.schemas.agent` — Agent + AgentVersion CRUD.
  * :mod:`agentforge_api.schemas.execution` — Execution create/retrieve.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Re-export the new submodules' public symbols so existing call
# sites can keep using ``from agentforge_api.schemas import …``.
from .agent import (  # noqa: F401
    AgentCreateIn,
    AgentOut,
    AgentVersionConfig,
    AgentVersionCreateIn,
    AgentVersionOut,
    AgentWithVersionsOut,
    GenerationConfig,
    ToolSpec,
)
from .execution import (  # noqa: F401
    ExecutionCreateIn,
    ExecutionEventOut,
    ExecutionOut,
    ExecutionWithEventsOut,
)


class HealthOut(BaseModel):
    """Health-check response."""

    status: str = "ok"
    version: str
    environment: str


class LoginIn(BaseModel):
    """Email + password login payload."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class TokenOut(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    """Public user representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    name: Optional[str] = None
    is_admin: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None


class DemoSessionOut(BaseModel):
    """Response body for ``POST /api/v1/demo/session``."""

    session_id: str
    expires_at: datetime
    demo_mode: bool = True


class DemoProjectOut(BaseModel):
    """Placeholder response for ``GET /api/v1/demo/project``.

    Real content lands in Phase 14. For now the API returns a static
    description so the recruiter demo route can be wired end-to-end.
    """

    title: str
    summary: str
    agents: list[str] = Field(default_factory=list)
    workflow: Optional[str] = None
    message: str = "Full demo content lands in Phase 14."


__all__ = [
    "AgentCreateIn",
    "AgentOut",
    "AgentVersionConfig",
    "AgentVersionCreateIn",
    "AgentVersionOut",
    "AgentWithVersionsOut",
    "DemoProjectOut",
    "DemoSessionOut",
    "ExecutionCreateIn",
    "ExecutionEventOut",
    "ExecutionOut",
    "ExecutionWithEventsOut",
    "GenerationConfig",
    "HealthOut",
    "LoginIn",
    "TokenOut",
    "ToolSpec",
    "UserOut",
]
