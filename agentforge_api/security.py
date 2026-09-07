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

"""Security helpers — password hashing and JWT encode/decode.

Phase 1 ships:
  * :func:`hash_password` / :func:`verify_password` using ``argon2``.
  * :func:`create_access_token` / :func:`decode_token` for JWTs.

Real production hardening (refresh token rotation, OAuth flows, API
key hashing, rate limiting) lands in Phase 13. The functions here are
deliberately minimal but use the real algorithms.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .config import get_settings


# ---------------------------------------------------------------------------
# Password hashing (Argon2id).
# ---------------------------------------------------------------------------

_HASHER = PasswordHasher()


def hash_password(plaintext: str) -> str:
    """Return a salted Argon2id hash of ``plaintext``."""
    return _HASHER.hash(plaintext)


def verify_password(plaintext: str, hashed: str) -> bool:
    """Return ``True`` iff ``plaintext`` matches ``hashed``.

    Re-hashing is intentionally not handled here; password rotation
    lives in Phase 13.
    """
    try:
        return _HASHER.verify(hashed, plaintext)
    except VerifyMismatchError:
        return False


# ---------------------------------------------------------------------------
# JWT helpers.
# ---------------------------------------------------------------------------


def create_access_token(
    subject: str,
    extra_claims: Dict[str, Any] | None = None,
    ttl_minutes: int | None = None,
) -> str:
    """Return a signed JWT for ``subject`` (typically a user id)."""
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    ttl = ttl_minutes or settings.jwt_access_ttl_minutes
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl)).timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Dict[str, Any]:
    """Decode a JWT, raising :class:`jwt.PyJWTError` on failure."""
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
