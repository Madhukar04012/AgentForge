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

"""FastAPI dependencies.

Phase 1 shipped a stub :func:`get_current_user` that returned a
fixed ``User`` only when a demo session was active. Phase 2 keeps
the same demo-aware shape but **also** resolves the user's
"default workspace" — every :class:`Agent` and :class:`Execution`
must belong to a workspace, and the workspace id is never taken
from the client. Real authentication (refresh tokens, OAuth, MFA)
lands in Phase 13.
"""

from __future__ import annotations

import re
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .db import get_db
from .models.workspace import User, Workspace, WorkspaceMember, WorkspaceRole


_SLUG_SAFE = re.compile(r"[^a-z0-9-]+")


def _slugify(value: str) -> str:
    """Lowercase, replace non-alnum with ``-``, collapse repeats."""
    value = value.lower().strip()
    value = _SLUG_SAFE.sub("-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "user"


def get_optional_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> Optional[User]:
    """Return the current user if a valid session cookie is present.

    Phase 1/2 behavior:

      * If a demo session is active (the request was issued by
        :func:`agentforge_api.middleware.mark_demo_request`, which
        sets ``request.state.is_demo = True``), return the bootstrap
        admin user.
      * Otherwise return ``None`` — the protected endpoints will
        then 401.
    """
    if not getattr(request.state, "is_demo", False):
        return None
    return db.query(User).filter(User.is_admin.is_(True)).first()


def get_current_user(
    user: Annotated[Optional[User], Depends(get_optional_user)],
) -> User:
    """FastAPI dependency that returns the current user or 401s."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_or_create_default_workspace(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Workspace:
    """Return the user's first workspace, creating a default if needed.

    The default workspace is named after the user's email local part
    and is owned by the user. If the user is a member of no
    workspace yet, we create one and add them as ``owner``. This is
    a Phase 2 convenience so the agents + executions endpoints work
    end-to-end without a separate "create workspace" flow. The real
    multi-tenant RBAC lands in Phase 13.
    """
    member = (
        db.query(WorkspaceMember)
        .filter(WorkspaceMember.user_id == user.id)
        .order_by(WorkspaceMember.invited_at.asc())
        .first()
    )
    if member is not None:
        workspace = (
            db.query(Workspace).filter(Workspace.id == member.workspace_id).first()
        )
        if workspace is not None:
            return workspace

    # No workspace yet — create a default one.
    local_part = (user.email or user.id).split("@", 1)[0]
    slug_base = _slugify(local_part)
    slug = slug_base
    suffix = 1
    while db.query(Workspace).filter(Workspace.slug == slug).first() is not None:
        suffix += 1
        slug = f"{slug_base}-{suffix}"

    workspace = Workspace(
        name=f"{user.name or local_part}'s workspace",
        slug=slug,
        owner_id=user.id,
    )
    db.add(workspace)
    db.flush()

    membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=user.id,
        role=WorkspaceRole.OWNER,
    )
    db.add(membership)
    db.commit()
    db.refresh(workspace)
    return workspace


# Re-export for convenience.
__all__ = [
    "get_current_user",
    "get_db",
    "get_optional_user",
    "get_or_create_default_workspace",
]
