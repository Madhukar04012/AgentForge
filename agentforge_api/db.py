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

"""SQLAlchemy engine, session factory, and declarative base.

Phase 1 ships a synchronous engine backed by SQLAlchemy 2.x. Later
phases may introduce an async engine, but the Phase 1 endpoints are
all read-light / write-light, so sync is sufficient and well-tested
on both SQLite (dev) and PostgreSQL (prod).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


def _build_engine_url(url: str) -> str:
    """SQLite needs ``check_same_thread=False`` when used by FastAPI."""
    if url.startswith("sqlite"):
        return url
    return url


# Module-level engine — created lazily on first call to ``get_engine``
# so tests can mutate ``Settings.db_url`` before the engine is built.
_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine():
    """Return the process-wide SQLAlchemy engine, creating it on demand."""
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        url = _build_engine_url(settings.db_url)
        connect_args = (
            {"check_same_thread": False} if url.startswith("sqlite") else {}
        )
        _engine = create_engine(
            url,
            echo=settings.db_echo,
            future=True,
            connect_args=connect_args,
        )
        _SessionLocal = sessionmaker(
            bind=_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return the session factory; build it on demand."""
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    return _SessionLocal


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a SQLAlchemy session.

    Usage::

        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...

    The session is closed automatically when the request finishes.
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Iterator[Session]:
    """Context-manager variant of :func:`get_db` for non-FastAPI code."""
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine_for_tests() -> None:
    """Drop the cached engine and session factory.

    Tests that swap ``Settings.db_url`` (e.g. to an in-memory SQLite)
    must call this before re-reading settings.
    """
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
