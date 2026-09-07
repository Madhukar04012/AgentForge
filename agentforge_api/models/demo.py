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

"""Demo session ORM model.

A ``DemoSession`` is a server-issued record that lets a recruiter
walk through a pre-seeded project without an API key. Phase 1 only
declares and persists the row; the pre-seeded workspace + project
land in Phase 14.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String

from ..db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class DemoSession(Base):
    """A short-lived anonymous session used by the recruiter demo."""

    __tablename__ = "demo_sessions"

    id = Column(String(36), primary_key=True, default=_uuid)
    seed_user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    ip_hash = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    executions_used = Column(String(8), nullable=False, default="0")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DemoSession id={self.id!r} expires_at={self.expires_at!r}>"
