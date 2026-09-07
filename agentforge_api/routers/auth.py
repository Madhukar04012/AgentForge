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

"""Auth router — placeholder login / logout.

Phase 1 ships a minimal email+password login that returns a JWT and a
logout endpoint that clears the session cookie. The real flow —
password rotation, refresh tokens, OAuth, MFA, account lockout —
lands in Phase 13.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from .. import __version__
from ..config import get_settings
from ..db import get_db
from ..models.workspace import User
from ..schemas import LoginIn, TokenOut, UserOut
from ..security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenOut,
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginIn,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> TokenOut:
    """Authenticate with email + password and return a JWT.

    The JWT is also set as an HTTP-only cookie so subsequent requests
    can authenticate via cookie or ``Authorization: Bearer`` header.
    """
    settings = get_settings()
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        # Generic message — do not leak whether the email exists.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user.last_login_at = datetime.now(tz=timezone.utc)
    db.add(user)
    db.commit()

    token = create_access_token(subject=user.id, extra_claims={"email": user.email})
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="lax",
        max_age=settings.jwt_access_ttl_minutes * 60,
    )
    return TokenOut(
        access_token=token,
        expires_in=settings.jwt_access_ttl_minutes * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    """Clear the session cookie. Idempotent."""
    settings = get_settings()
    response.delete_cookie(settings.session_cookie_name)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


# Re-exported for tests.
__all__ = ["router"]
