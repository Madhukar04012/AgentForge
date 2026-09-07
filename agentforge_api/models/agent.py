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

"""Agent + AgentVersion ORM models.

A :class:`Agent` is a logical, named entity in a workspace. Its
configuration is held in :class:`AgentVersion` rows, which are
**immutable** — every configuration change creates a new version
row. The runtime always executes against a specific version, so
historical executions remain reproducible even as the agent's
"current" configuration evolves.

The version config is stored as JSON for forward compatibility: new
fields (e.g. output schemas, response schemas) can be added without
a schema migration. The :mod:`agentforge_api.schemas.agent` Pydantic
model validates the JSON shape on read and on create.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class Agent(Base):
    """A logical, named agent within a workspace."""

    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint("workspace_id", "name", name="agents_workspace_name_uniq"),
        Index("ix_agents_workspace_id", "workspace_id"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    workspace_id = Column(
        String(36),
        ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    current_version_id = Column(
        String(36),
        ForeignKey("agent_versions.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_now,
        onupdate=_now,
    )

    versions = relationship(
        "AgentVersion",
        back_populates="agent",
        cascade="all, delete-orphan",
        foreign_keys="AgentVersion.agent_id",
        order_by="AgentVersion.version_number",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<Agent id={self.id!r} name={self.name!r}>"


class AgentVersion(Base):
    """Immutable snapshot of an agent's configuration.

    Rows are INSERT-ONLY — the API and runtime never ``UPDATE`` an
    existing row. Changing a configuration creates a new
    :class:`AgentVersion` (with ``version_number`` incremented) and
    points the parent :class:`Agent.current_version_id` at it.

    ``config`` is a JSON blob whose shape is described by
    :class:`agentforge_api.schemas.agent.AgentVersionConfig`. The
    database does not validate the JSON contents — that's done at
    the API boundary by the Pydantic schema. This is intentional:
    it lets the schema evolve without DB migrations.
    """

    __tablename__ = "agent_versions"
    __table_args__ = (
        UniqueConstraint(
            "agent_id", "version_number", name="agent_versions_agent_version_uniq"
        ),
        Index("ix_agent_versions_agent_id", "agent_id"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    agent_id = Column(
        String(36),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number = Column(Integer, nullable=False)
    # The actual config: model_provider, model_name, system_prompt,
    # tools (list[dict]), generation_config (dict), and any future
    # fields. Validated by Pydantic at the API boundary.
    config = Column(JSON, nullable=False)
    # The user-friendly change note shown in the UI.
    change_note = Column(Text, nullable=True)
    created_by_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    agent = relationship(
        "Agent", back_populates="versions", foreign_keys=[agent_id]
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AgentVersion id={self.id!r} "
            f"agent_id={self.agent_id!r} version={self.version_number}>"
        )
