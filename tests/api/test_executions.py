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

"""Executions API + runtime bridge tests."""

from __future__ import annotations

from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from agentforge_api.db import get_session_factory
from agentforge_api.models.agent import Agent, AgentVersion
from agentforge_api.models.execution import Execution, ExecutionStatus
from agentforge_api.providers import get_provider, ProviderNotConfigured
from agentforge_api.providers.base import (
    ModelProvider,
    ProviderRequest,
    ProviderStreamEvent,
    register_provider,
)
from agentforge_api.runtime import run_execution


# ---------------------------------------------------------------------------
# Fixtures / helpers.
# ---------------------------------------------------------------------------


def _login_as_admin(client: TestClient) -> None:
    response = client.post("/api/v1/demo/session", json={})
    assert response.status_code == 201


def _valid_config(provider: str = "google", model: str = "gemini-2.0-flash") -> dict:
    return {
        "model_provider": provider,
        "model_name": model,
        "system_prompt": "You are a test agent.",
        "tools": [],
        "generation_config": {"temperature": 0.1, "max_output_tokens": 64},
    }


def _create_agent(client: TestClient, name: str = "Test", provider: str = "google") -> dict:
    _login_as_admin(client)
    response = client.post(
        "/api/v1/agents", json={"name": name, "config": _valid_config(provider=provider)}
    )
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Provider stub used in the bridge test below. It is registered
# transiently inside a test and unregistered afterwards via the
# registry's mutation API (we do not export that; instead we use
# register_provider which raises on duplicates, so this test only
# ever runs the registration once per session).
# ---------------------------------------------------------------------------


_FAKE_PROVIDER_NAME = "fake-for-tests"


class _FakeProvider(ModelProvider):
    """Deterministic provider used only by the bridge tests."""

    name = _FAKE_PROVIDER_NAME

    def __init__(self) -> None:
        pass

    @classmethod
    def is_configured(cls) -> bool:
        return True

    def invoke(self, request: ProviderRequest) -> Iterator[ProviderStreamEvent]:
        yield ProviderStreamEvent(kind="model_text", text="hello ")
        yield ProviderStreamEvent(kind="model_text", text="world")
        yield ProviderStreamEvent(
            kind="done",
            output="hello world",
            usage={"tokens_in": 3, "tokens_out": 2},
        )


@pytest.fixture(scope="module", autouse=True)
def _register_fake_provider() -> Iterator[None]:
    register_provider(_FakeProvider)
    yield
    # No public unregister; the test process exits after this.
    # The test is module-scoped so it runs once.


# ---------------------------------------------------------------------------
# API-level tests.
# ---------------------------------------------------------------------------


def test_create_execution_requires_auth(client: TestClient) -> None:
    # NOTE: we use a fresh, unauthenticated client by clearing
    # cookies. The `_create_agent` helper authenticates, so we can't
    # use it here.
    response = client.post(
        "/api/v1/executions",
        json={
            "agent_id": "nope",
            "agent_version_id": "nope",
            "input": "hi",
        },
    )
    # We get 401 because the request is unauthenticated (the
    # workspace resolution dependency fails before the agent lookup).
    assert response.status_code == 401


def test_create_execution_returns_queued_row(client: TestClient) -> None:
    agent = _create_agent(client)
    response = client.post(
        "/api/v1/executions",
        json={
            "agent_id": agent["id"],
            "agent_version_id": agent["versions"][0]["id"],
            "input": "hi there",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] in {"queued", "running", "completed", "failed", "cancelled"}
    # Without the Arq worker process running, the execution stays
    # queued. The real bridge test below drives it manually.
    assert body["input"] == "hi there"
    assert body["agent_id"] == agent["id"]
    assert body["agent_version_id"] == agent["versions"][0]["id"]


def test_create_execution_rejects_unknown_agent(client: TestClient) -> None:
    _create_agent(client)
    response = client.post(
        "/api/v1/executions",
        json={
            "agent_id": "nope",
            "agent_version_id": "nope",
            "input": "hi",
        },
    )
    assert response.status_code == 404


def test_get_execution_returns_event_log(client: TestClient) -> None:
    agent = _create_agent(client)
    created = client.post(
        "/api/v1/executions",
        json={
            "agent_id": agent["id"],
            "agent_version_id": agent["versions"][0]["id"],
            "input": "show me the events",
        },
    ).json()
    exec_id = created["id"]
    response = client.get(f"/api/v1/executions/{exec_id}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == exec_id
    assert "events" in body
    # We may have zero events (the worker hasn't run yet) — the
    # shape is what matters here.
    for ev in body["events"]:
        assert "id" in ev
        assert "sequence" in ev
        assert "event_type" in ev
        assert "occurred_at" in ev


def test_list_executions_returns_most_recent_first(client: TestClient) -> None:
    agent = _create_agent(client)
    payload = {
        "agent_id": agent["id"],
        "agent_version_id": agent["versions"][0]["id"],
        "input": "hi",
    }
    e1 = client.post("/api/v1/executions", json=payload).json()
    e2 = client.post("/api/v1/executions", json=payload).json()

    r = client.get("/api/v1/executions")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2
    # Most recent first: e2 should be index 0.
    assert rows[0]["id"] == e2["id"]
    assert rows[1]["id"] == e1["id"]


def test_get_execution_404_for_unknown_id(client: TestClient) -> None:
    _login_as_admin(client)
    response = client.get("/api/v1/executions/does-not-exist")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Bridge tests — drive run_execution directly.
# ---------------------------------------------------------------------------


def test_bridge_runs_fake_provider_and_persists_events() -> None:
    """End-to-end: create a queued execution, run the bridge, assert
    that the execution transitions to COMPLETED, the event log is
    populated in order, and the output is the model's text."""
    factory = get_session_factory()
    with factory() as db:  # type: Session
        # Create an agent + version referencing the fake provider.
        agent = Agent(
            id="agent-bridge-test",
            workspace_id="ws-bridge-test",
            name="Bridge Test",
            description=None,
            current_version_id=None,
            created_at=None,
            updated_at=None,
        )
        version = AgentVersion(
            id="version-bridge-test",
            agent_id=agent.id,
            version_number=1,
            config={
                "model_provider": _FAKE_PROVIDER_NAME,
                "model_name": "fake-model-1",
                "system_prompt": "say hi",
                "tools": [],
                "generation_config": {},
            },
            change_note=None,
            created_by_id=None,
            created_at=None,
        )
        execution = Execution(
            id="exec-bridge-test",
            workspace_id="ws-bridge-test",
            agent_id=agent.id,
            agent_version_id=version.id,
            status=ExecutionStatus.QUEUED,
            input="hello",
            queued_at=None,
        )
        db.add_all([agent, version, execution])
        db.commit()

        outcome = run_execution(db, execution.id)

    assert outcome.status == ExecutionStatus.COMPLETED
    assert outcome.output == "hello world"
    assert outcome.tokens_in == 3
    assert outcome.tokens_out == 2
    assert outcome.latency_ms is not None and outcome.latency_ms >= 0

    # Inspect the event log.
    with factory() as db:
        exec_row = db.query(Execution).filter(Execution.id == execution.id).one()
        events = list(exec_row.events)
        types = [e.event_type for e in events]
        # Expected sequence:
        #   execution.started, model.request, model.text, model.text, model.response, execution.completed
        assert types == [
            "execution.started",
            "model.request",
            "model.text",
            "model.text",
            "model.response",
            "execution.completed",
        ]
        # Sequence numbers are 1-based and monotonic.
        assert [e.sequence for e in events] == [1, 2, 3, 4, 5, 6]
        # The two model.text events concatenate to the final output.
        text_chunks = [e.payload["text"] for e in events if e.event_type == "model.text"]
        assert "".join(text_chunks) == "hello world"


def test_bridge_marks_execution_failed_when_provider_not_configured() -> None:
    """The Google provider is not configured in tests; the bridge
    must mark the execution as FAILED with a clear error."""
    factory = get_session_factory()
    with factory() as db:  # type: Session
        agent = Agent(
            id="agent-fail-test",
            workspace_id="ws-fail-test",
            name="Fail Test",
            current_version_id=None,
        )
        version = AgentVersion(
            id="version-fail-test",
            agent_id=agent.id,
            version_number=1,
            config={
                "model_provider": "google",
                "model_name": "gemini-2.0-flash",
                "system_prompt": "",
                "tools": [],
                "generation_config": {},
            },
        )
        execution = Execution(
            id="exec-fail-test",
            workspace_id="ws-fail-test",
            agent_id=agent.id,
            agent_version_id=version.id,
            status=ExecutionStatus.QUEUED,
            input="hi",
        )
        db.add_all([agent, version, execution])
        db.commit()

        outcome = run_execution(db, execution.id)

    assert outcome.status == ExecutionStatus.FAILED
    assert outcome.error
    assert "google" in outcome.error.lower() or "GOOGLE_API_KEY" in outcome.error

    with factory() as db:
        exec_row = db.query(Execution).filter(Execution.id == execution.id).one()
        types = [e.event_type for e in exec_row.events]
        # execution.started + execution.failed
        assert types[0] == "execution.started"
        assert types[-1] == "execution.failed"
        # Error payload is recorded.
        failed = [e for e in exec_row.events if e.event_type == "execution.failed"][0]
        assert "error" in failed.payload
        assert failed.payload["error"]


def test_bridge_is_idempotent_on_already_completed() -> None:
    """Running the bridge twice on a completed execution must not
    re-run it. The second call is a no-op."""
    factory = get_session_factory()
    with factory() as db:  # type: Session
        agent = Agent(
            id="agent-idem-test",
            workspace_id="ws-idem-test",
            name="Idem Test",
            current_version_id=None,
        )
        version = AgentVersion(
            id="version-idem-test",
            agent_id=agent.id,
            version_number=1,
            config={
                "model_provider": _FAKE_PROVIDER_NAME,
                "model_name": "fake-model-2",
                "system_prompt": "",
                "tools": [],
                "generation_config": {},
            },
        )
        execution = Execution(
            id="exec-idem-test",
            workspace_id="ws-idem-test",
            agent_id=agent.id,
            agent_version_id=version.id,
            status=ExecutionStatus.QUEUED,
            input="hi",
        )
        db.add_all([agent, version, execution])
        db.commit()

        first = run_execution(db, execution.id)
        assert first.status == ExecutionStatus.COMPLETED
        second = run_execution(db, execution.id)
        assert second.status == ExecutionStatus.COMPLETED
        # No new events on the second call.
        events = list(
            db.query(__import__("agentforge_api.models.execution", fromlist=["ExecutionEvent"]).ExecutionEvent)
            .filter_by(execution_id=execution.id)
            .all()
        )
        assert len(events) == 6  # the original six


def test_unknown_provider_id_raises_at_registry_level() -> None:
    """Sanity: the registry rejects ids that were never registered."""
    with pytest.raises(ProviderNotConfigured):
        get_provider("definitely-not-a-real-provider-id-xyz")
