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

"""Pydantic schemas for the Agent + AgentVersion API.

The :class:`AgentVersionConfig` schema is what we **write to** the
``agent_versions.config`` JSON column. The DB column is JSON so we
can evolve the schema without a migration, but the API boundary
strictly validates every payload with ``extra="forbid"`` so we
catch typos at the door.

The Pydantic model mirrors the spec:

  * ``model_provider`` — one of the registered provider ids.
  * ``model_name`` — provider-specific (e.g. ``"gemini-2.0-flash"``).
  * ``system_prompt`` — the agent's instruction text.
  * ``tools`` — list of provider-agnostic tool specs (Phase 2: empty).
  * ``generation_config`` — provider-agnostic knobs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class GenerationConfig(BaseModel):
    """Provider-agnostic generation knobs.

    Unknown fields are rejected via ``extra="forbid"``. Providers
    may accept additional fields in future schema versions; when
    that happens, add the field here and bump the API.
    """

    model_config = ConfigDict(extra="forbid")

    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_output_tokens: Optional[int] = Field(default=None, ge=1, le=100_000)


class ToolSpec(BaseModel):
    """Provider-agnostic tool spec.

    Phase 2 ships an empty list. Future phases (the workflow engine
    in Phase 4, GitHub + Docker in Phase 11) will add concrete
    shapes (e.g. ``{"type": "function", "name": ..., "parameters": ...}``).
    """

    model_config = ConfigDict(extra="forbid")

    type: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=128)


class AgentVersionConfig(BaseModel):
    """Configuration stored in ``agent_versions.config``.

    Validated both on create and on read. If the DB row contains
    a value that does not match this schema, reads fail loudly
    rather than silently dropping fields.
    """

    model_config = ConfigDict(extra="forbid")

    model_provider: str = Field(min_length=1, max_length=64)
    model_name: str = Field(min_length=1, max_length=128)
    system_prompt: str = Field(default="", max_length=32_000)
    tools: List[ToolSpec] = Field(default_factory=list, max_length=64)
    generation_config: GenerationConfig = Field(default_factory=GenerationConfig)


class AgentCreateIn(BaseModel):
    """Request body for ``POST /api/v1/agents``."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    # The initial version's config. We require it on create so
    # every agent has at least one version and is runnable.
    config: AgentVersionConfig
    change_note: Optional[str] = Field(default=None, max_length=2000)


class AgentVersionCreateIn(BaseModel):
    """Request body for ``POST /api/v1/agents/{id}/versions``."""

    model_config = ConfigDict(extra="forbid")

    config: AgentVersionConfig
    change_note: Optional[str] = Field(default=None, max_length=2000)


class AgentOut(BaseModel):
    """Public agent representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    current_version_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AgentVersionOut(BaseModel):
    """Public agent-version representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    agent_id: str
    version_number: int
    config: AgentVersionConfig
    change_note: Optional[str] = None
    created_at: datetime


class AgentWithVersionsOut(AgentOut):
    """Agent + its version list. Returned by ``GET /agents/{id}``."""

    versions: List[AgentVersionOut] = Field(default_factory=list)


__all__ = [
    "AgentCreateIn",
    "AgentOut",
    "AgentVersionConfig",
    "AgentVersionCreateIn",
    "AgentVersionOut",
    "AgentWithVersionsOut",
    "GenerationConfig",
    "ToolSpec",
]
