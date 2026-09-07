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

"""Pydantic schemas for the executions API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ExecutionCreateIn(BaseModel):
    """Request body for ``POST /api/v1/executions``.

    The client must specify which :class:`AgentVersion` to run
    against. We never accept an "agent id only" request: the
    runtime must always know the exact version.
    """

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(min_length=1, max_length=36)
    agent_version_id: str = Field(min_length=1, max_length=36)
    input: str = Field(min_length=1, max_length=64_000)


class ExecutionEventOut(BaseModel):
    """Single persisted :class:`ExecutionEvent`."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    sequence: int
    event_type: str
    payload: Optional[Dict[str, Any]] = None
    occurred_at: datetime


class ExecutionOut(BaseModel):
    """Public execution representation (without event log)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    agent_id: str
    agent_version_id: str
    status: str
    input: str
    output: Optional[str] = None
    error: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_usd: Optional[float] = None
    latency_ms: Optional[int] = None
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    triggered_by_id: Optional[str] = None


class ExecutionWithEventsOut(ExecutionOut):
    """Execution + its event log. Returned by ``GET /executions/{id}``."""

    events: List[ExecutionEventOut] = Field(default_factory=list)


__all__ = [
    "ExecutionCreateIn",
    "ExecutionEventOut",
    "ExecutionOut",
    "ExecutionWithEventsOut",
]
