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

"""Execution + ExecutionEvent ORM models.

A :class:`Execution` is a single attempt to run an
:class:`AgentVersion` with a specific user-provided input. The
execution always references the **exact** ``agent_version_id`` it
ran against — never the agent's mutable ``current_version_id`` —
so historical executions remain reproducible.

:class:`ExecutionEvent` is the append-only event log for an
execution. Events are produced by the runtime bridge and the worker;
the API streams them to the UI for live updates.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class ExecutionStatus(str, enum.Enum):
    """Lifecycle states for an :class:`Execution`."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Execution(Base):
    """A single attempt to run an AgentVersion with a user input."""

    __tablename__ = "executions"
    __table_args__ = (
        Index("ix_executions_workspace_id", "workspace_id"),
        Index("ix_executions_agent_version_id", "agent_version_id"),
        Index("ix_executions_status", "status"),
        Index("ix_executions_queued_at", "queued_at"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    workspace_id = Column(
        String(36),
        ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False,
    )
    agent_id = Column(
        String(36),
        ForeignKey("agents.id", ondelete="RESTRICT"),
        nullable=False,
    )
    agent_version_id = Column(
        String(36),
        ForeignKey("agent_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status = Column(
        SAEnum(ExecutionStatus, name="execution_status"),
        nullable=False,
        default=ExecutionStatus.QUEUED,
    )
    # The user input, stored as a string for Phase 2. The schema
    # can be extended to support multi-modal inputs (Content[]
    # matching ADK) without breaking the table.
    input = Column(Text, nullable=False)
    # Final model output, when status == COMPLETED.
    output = Column(Text, nullable=True)
    # Error message, when status == FAILED.
    error = Column(Text, nullable=True)
    # Token / cost accounting. Populated by the runtime bridge when
    # the provider reports it.
    tokens_in = Column(Integer, nullable=True)
    tokens_out = Column(Integer, nullable=True)
    cost_usd = Column(Float, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    # Timing.
    queued_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    # User attribution.
    triggered_by_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    events = relationship(
        "ExecutionEvent",
        back_populates="execution",
        cascade="all, delete-orphan",
        order_by="ExecutionEvent.sequence",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Execution id={self.id!r} status={self.status!r}>"


class ExecutionEvent(Base):
    """A single event emitted during an execution's lifecycle."""

    __tablename__ = "execution_events"
    __table_args__ = (
        Index("ix_execution_events_execution_id", "execution_id"),
        # sequence is monotonic per execution, used for ordering +
        # de-duplication.
        Index("ix_execution_events_exec_seq", "execution_id", "sequence"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    execution_id = Column(
        String(36),
        ForeignKey("executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence = Column(Integer, nullable=False)
    event_type = Column(String(64), nullable=False)
    # Event payload. Kept as JSON so the event model can grow without
    # schema migrations; the API layer validates the shape.
    payload = Column(JSON, nullable=True)
    # Free-form timestamp (some events arrive from upstream that
    # already has a wall-clock; we keep that here).
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    execution = relationship("Execution", back_populates="events")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ExecutionEvent exec={self.execution_id!r} "
            f"seq={self.sequence} type={self.event_type!r}>"
        )
