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

"""Agents + AgentVersions router.

Implements:

  * ``POST /api/v1/agents`` — create an agent and its initial
    version. The initial version is required (we never create an
    agent with zero versions).
  * ``GET  /api/v1/agents`` — list agents in the caller's
    workspace.
  * ``GET  /api/v1/agents/{id}`` — fetch a single agent with all
    its versions.
  * ``POST /api/v1/agents/{id}/versions`` — create a new version
    for an existing agent. Versions are immutable — the previous
    version is never overwritten.
  * ``GET  /api/v1/agents/{id}/versions/{vid}`` — fetch one
    specific version.

All endpoints enforce workspace ownership: a request is only
allowed to read or mutate agents that belong to the caller's
default workspace. The workspace id is **never** taken from the
client; it is resolved from the authenticated user.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_or_create_default_workspace
from ..models.agent import Agent, AgentVersion
from ..models.workspace import User, Workspace
from ..providers import registered_provider_ids
from ..schemas.agent import (
    AgentCreateIn,
    AgentOut,
    AgentVersionConfig,
    AgentVersionCreateIn,
    AgentVersionOut,
    AgentWithVersionsOut,
)

router = APIRouter(prefix="/agents", tags=["agents"])


def _validate_provider_id(model_provider: str) -> None:
    """Reject unknown provider ids at the API boundary."""
    if model_provider not in registered_provider_ids():
        # Use the integer literal to stay compatible across Starlette
        # versions that renamed HTTP_422_UNPROCESSABLE_ENTITY to
        # HTTP_422_UNPROCESSABLE_CONTENT.
        raise HTTPException(
            status_code=422,
            detail=(
                f"Unknown model_provider {model_provider!r}. "
                f"Known providers: {registered_provider_ids()}"
            ),
        )


def _next_version_number(db: Session, agent_id: str) -> int:
    """Return the next version number for the given agent."""
    latest = (
        db.query(AgentVersion)
        .filter(AgentVersion.agent_id == agent_id)
        .order_by(AgentVersion.version_number.desc())
        .first()
    )
    return (latest.version_number + 1) if latest else 1


def _load_agent_for_workspace(
    db: Session, workspace_id: str, agent_id: str
) -> Agent:
    agent = (
        db.query(Agent).filter(Agent.id == agent_id).one_or_none()
    )
    if agent is None or agent.workspace_id != workspace_id:
        # Do not leak whether the agent exists in another workspace.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return agent


# ---------------------------------------------------------------------------
# Routes.
# ---------------------------------------------------------------------------


@router.get("", response_model=List[AgentOut])
def list_agents(
    db: Annotated[Session, Depends(get_db)],
    workspace: Annotated[Workspace, Depends(get_or_create_default_workspace)],
) -> list[AgentOut]:
    """List agents in the caller's workspace, most recent first."""
    rows = (
        db.query(Agent)
        .filter(Agent.workspace_id == workspace.id)
        .order_by(Agent.updated_at.desc())
        .all()
    )
    return [AgentOut.model_validate(r) for r in rows]


@router.post(
    "", response_model=AgentWithVersionsOut, status_code=status.HTTP_201_CREATED
)
def create_agent(
    payload: AgentCreateIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    workspace: Annotated[Workspace, Depends(get_or_create_default_workspace)],
) -> AgentWithVersionsOut:
    """Create an agent and its initial version.

    The Pydantic schema has already validated the config; we do one
    extra check here for the provider id because the schema
    (intentionally) is provider-agnostic.
    """
    _validate_provider_id(payload.config.model_provider)

    now = datetime.now(tz=timezone.utc)
    agent = Agent(
        workspace_id=workspace.id,
        name=payload.name,
        description=payload.description,
        current_version_id=None,  # wired below
        created_at=now,
        updated_at=now,
    )
    db.add(agent)
    db.flush()  # populate agent.id

    version = AgentVersion(
        agent_id=agent.id,
        version_number=1,
        config=payload.config.model_dump(),
        change_note=payload.change_note or "Initial version",
        created_by_id=user.id,
        created_at=now,
    )
    db.add(version)
    db.flush()

    agent.current_version_id = version.id
    agent.updated_at = now
    db.commit()
    db.refresh(agent)
    db.refresh(version)

    return AgentWithVersionsOut(
        id=agent.id,
        workspace_id=agent.workspace_id,
        name=agent.name,
        description=agent.description,
        current_version_id=agent.current_version_id,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        versions=[AgentVersionOut.model_validate(version)],
    )


@router.get("/{agent_id}", response_model=AgentWithVersionsOut)
def get_agent(
    agent_id: str,
    db: Annotated[Session, Depends(get_db)],
    workspace: Annotated[Workspace, Depends(get_or_create_default_workspace)],
) -> AgentWithVersionsOut:
    agent = _load_agent_for_workspace(db, workspace.id, agent_id)
    versions = (
        db.query(AgentVersion)
        .filter(AgentVersion.agent_id == agent.id)
        .order_by(AgentVersion.version_number.desc())
        .all()
    )
    return AgentWithVersionsOut(
        id=agent.id,
        workspace_id=agent.workspace_id,
        name=agent.name,
        description=agent.description,
        current_version_id=agent.current_version_id,
        created_at=agent.created_at,
        updated_at=agent.updated_at,
        versions=[AgentVersionOut.model_validate(v) for v in versions],
    )


@router.post(
    "/{agent_id}/versions",
    response_model=AgentVersionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_agent_version(
    agent_id: str,
    payload: AgentVersionCreateIn,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    workspace: Annotated[Workspace, Depends(get_or_create_default_workspace)],
) -> AgentVersionOut:
    """Create a new immutable version for an existing agent."""
    _validate_provider_id(payload.config.model_provider)
    agent = _load_agent_for_workspace(db, workspace.id, agent_id)

    next_number = _next_version_number(db, agent.id)
    now = datetime.now(tz=timezone.utc)
    version = AgentVersion(
        agent_id=agent.id,
        version_number=next_number,
        config=payload.config.model_dump(),
        change_note=payload.change_note,
        created_by_id=user.id,
        created_at=now,
    )
    db.add(version)
    db.flush()

    # Point the agent's current_version_id at the latest version.
    agent.current_version_id = version.id
    agent.updated_at = now
    db.commit()
    db.refresh(version)

    return AgentVersionOut.model_validate(version)


@router.get(
    "/{agent_id}/versions/{version_id}", response_model=AgentVersionOut
)
def get_agent_version(
    agent_id: str,
    version_id: str,
    db: Annotated[Session, Depends(get_db)],
    workspace: Annotated[Workspace, Depends(get_or_create_default_workspace)],
) -> AgentVersionOut:
    agent = _load_agent_for_workspace(db, workspace.id, agent_id)
    version = (
        db.query(AgentVersion)
        .filter(
            AgentVersion.id == version_id, AgentVersion.agent_id == agent.id
        )
        .one_or_none()
    )
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent version not found",
        )
    return AgentVersionOut.model_validate(version)


__all__ = ["router"]
