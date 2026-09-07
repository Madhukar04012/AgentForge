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

"""Shared pytest fixtures for the Phase 1 API tests.

Every test uses an isolated in-memory SQLite database so the test
suite has no external dependencies (no Postgres, no Redis). The
settings are reset before each test so module-level caching in
:mod:`agentforge_api.config` does not leak between tests.
"""

from __future__ import annotations

import os
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import Session, sessionmaker

# Configure the environment BEFORE importing the app. The app is
# instantiated at import time, so we set these env vars first.
os.environ.setdefault("AGENTFORGE_DB_URL", "sqlite:///:memory:")
os.environ.setdefault("AGENTFORGE_JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("AGENTFORGE_DEMO_MODE", "true")
# Use ``development`` (not ``test``) so cookies are NOT marked
# ``Secure`` — the TestClient speaks plain HTTP, and httpx refuses
# to send a Secure cookie back over an http:// connection.
os.environ.setdefault("AGENTFORGE_ENVIRONMENT", "development")


from agentforge_api import config as _config  # noqa: E402
from agentforge_api import db as _db  # noqa: E402
from agentforge_api.app import create_app  # noqa: E402
from agentforge_api.models.workspace import User  # noqa: E402
from agentforge_api.security import hash_password  # noqa: E402


@pytest.fixture(autouse=True)
def reset_settings_and_db() -> Iterator[None]:
    """Reset settings cache and engine before every test.

    We point the SQLAlchemy engine at a private in-memory SQLite (with
    a shared connection so multiple sessions can see the same data)
    and re-create the schema from the Base metadata.
    """
    _config._reset_settings_cache()
    _db.reset_engine_for_tests()

    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(
        bind=test_engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    _db.Base.metadata.create_all(bind=test_engine)

    # Monkey-patch the lazy module-level accessors so the app uses
    # our test engine / factory.
    _db._engine = test_engine  # type: ignore[attr-defined]
    _db._SessionLocal = TestingSessionLocal  # type: ignore[attr-defined]

    # Seed a bootstrap admin user so the auth + demo endpoints can
    # resolve ``get_optional_user`` and the ``seed_user`` lookup.
    with TestingSessionLocal() as session:  # type: Session
        admin = User(
            email="admin@agentforge.example.com",
            password_hash=hash_password("not-a-real-password"),
            name="Bootstrap Admin",
            is_admin=True,
            is_active=True,
        )
        session.add(admin)
        session.commit()

    yield

    # Tear down — drop the schema so the next test starts clean.
    _db.Base.metadata.drop_all(bind=test_engine)
    _db.reset_engine_for_tests()


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Return a FastAPI test client bound to the test app."""
    app = create_app()
    with TestClient(app) as c:
        yield c
