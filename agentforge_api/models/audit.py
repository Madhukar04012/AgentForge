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

"""Audit log ORM model.

A single append-only table for every mutating API call. Phase 1 only
declares the table; writes land when the auth router matures in
Phase 13.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from ..db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


# Use JSONB on PostgreSQL for performance; fall back to JSON on SQLite.
_JsonType = JSONB().with_variant(JSON(), "sqlite")


class AuditLog(Base):
    """An append-only audit record."""

    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=_uuid)
    workspace_id = Column(
        String(36),
        ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    actor_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    kind = Column(String(64), nullable=False, index=True)
    target_type = Column(String(64), nullable=True)
    target_id = Column(String(64), nullable=True)
    payload = Column(_JsonType, nullable=True)
    ip = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<AuditLog id={self.id!r} kind={self.kind!r}>"
