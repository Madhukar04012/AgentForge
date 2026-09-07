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

"""User / Workspace ORM models.

These tables are the multi-tenant primitives used by every later
phase. ``User`` carries a hashed password (Argon2id) and an
``is_admin`` flag; ``Workspace`` is the tenant root;
``WorkspaceMember`` is the join table with a role enum.

Phase 1 only persists and reads these tables; no business endpoints
list or mutate them yet (those land in Phase 13).
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from ..db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class WorkspaceRole(str, enum.Enum):
    """Membership role within a workspace."""

    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class User(Base):
    """A platform user."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_uuid)
    email = Column(String(320), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(120), nullable=True)
    avatar_url = Column(String(2048), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_now,
        onupdate=_now,
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    memberships = relationship(
        "WorkspaceMember",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="WorkspaceMember.user_id",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<User id={self.id!r} email={self.email!r}>"


class Workspace(Base):
    """A tenant root. All projects live under a workspace."""

    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(120), nullable=False)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    plan = Column(String(32), nullable=False, default="free")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_now,
        onupdate=_now,
    )

    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Workspace id={self.id!r} slug={self.slug!r}>"


class WorkspaceMember(Base):
    """A user's role within a workspace."""

    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="workspace_members_pk"),
    )

    workspace_id = Column(
        String(36),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role = Column(
        SAEnum(WorkspaceRole, name="workspace_role"),
        nullable=False,
        default=WorkspaceRole.VIEWER,
    )
    invited_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    invited_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="memberships", foreign_keys=[user_id])

    def __repr__(self) -> str:  # pragma: no cover
        return f"<WorkspaceMember ws={self.workspace_id!r} user={self.user_id!r} role={self.role!r}>"
