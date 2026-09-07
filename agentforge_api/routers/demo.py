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

"""Recruiter demo router.

* ``POST /api/v1/demo/session`` — issues a short-lived signed cookie
  and persists a :class:`DemoSession` row. Marks the request as
  "demo" so :class:`DemoModeMiddleware` can attach
  ``X-Demo-Mode: 1`` to subsequent responses.
* ``GET  /api/v1/demo/project`` — returns the seed project summary
  the demo route will render. Phase 1 returns a static placeholder;
  full content lands in Phase 14.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..middleware import mark_demo_request
from ..models.demo import DemoSession
from ..models.workspace import User
from ..schemas import DemoProjectOut, DemoSessionOut

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/session", response_model=DemoSessionOut, status_code=201)
def create_demo_session(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> DemoSessionOut:
    """Issue a demo session cookie and persist a :class:`DemoSession`."""
    settings = get_settings()
    if not settings.demo_mode:
        # In production with demo mode off, the endpoint should still
        # exist but always be a no-op; we return 404 to be honest.
        from fastapi import HTTPException, status as _status

        raise HTTPException(
            status_code=_status.HTTP_404_NOT_FOUND,
            detail="Demo mode is disabled",
        )

    # Phase 1: there is exactly one bootstrap user (the seeded admin).
    seed_user = db.query(User).filter(User.is_admin.is_(True)).first()

    now = datetime.now(tz=timezone.utc)
    expires = now + timedelta(minutes=settings.demo_session_ttl_minutes)
    session = DemoSession(
        seed_user_id=seed_user.id if seed_user else None,
        ip_hash=None,
        created_at=now,
        expires_at=expires,
        last_seen_at=now,
        executions_used="0",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Cookie.
    response.set_cookie(
        key=settings.demo_cookie_name,
        value=session.id,
        httponly=True,
        secure=settings.environment != "development",
        samesite="lax",
        max_age=settings.demo_session_ttl_minutes * 60,
    )
    mark_demo_request(request)

    return DemoSessionOut(
        session_id=session.id,
        expires_at=expires,
        demo_mode=True,
    )


@router.get("/project", response_model=DemoProjectOut)
def read_demo_project() -> DemoProjectOut:
    """Return the demo project's placeholder summary.

    Phase 1 returns a static description; full content (pre-computed
    traces + evaluation results) lands in Phase 14.
    """
    return DemoProjectOut(
        title="Compress verbose text into terse grunts",
        summary=(
            "A two-agent workflow that rewrites verbose prose into terse, "
            "caveman-style grunts and validates the result."
        ),
        agents=["compressor_v1", "validator_v1"],
        workflow="compress_and_validate",
    )
