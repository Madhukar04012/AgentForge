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

"""Agent + AgentVersion API tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def _login_as_admin(client: TestClient) -> None:
    """The demo session cookie authenticates the bootstrap admin."""
    response = client.post("/api/v1/demo/session", json={})
    assert response.status_code == 201, response.text


def _valid_config() -> dict:
    return {
        "model_provider": "google",
        "model_name": "gemini-2.0-flash",
        "system_prompt": "You are a helpful test agent.",
        "tools": [],
        "generation_config": {"temperature": 0.2, "max_output_tokens": 256},
    }


def test_create_agent_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/agents",
        json={"name": "x", "config": _valid_config()},
    )
    assert response.status_code == 401


def test_create_agent_succeeds(client: TestClient) -> None:
    _login_as_admin(client)
    response = client.post(
        "/api/v1/agents",
        json={"name": "Compressor", "config": _valid_config()},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["id"]
    assert body["name"] == "Compressor"
    assert body["current_version_id"]
    assert len(body["versions"]) == 1
    v = body["versions"][0]
    assert v["version_number"] == 1
    assert v["config"]["model_provider"] == "google"
    assert v["config"]["model_name"] == "gemini-2.0-flash"


def test_create_agent_rejects_unknown_provider(client: TestClient) -> None:
    _login_as_admin(client)
    bad_config = _valid_config()
    bad_config["model_provider"] = "not-a-real-provider"
    response = client.post(
        "/api/v1/agents", json={"name": "x", "config": bad_config}
    )
    # FastAPI's 422 happens at the body-validation layer when the
    # payload fails the Pydantic schema. We don't catch unknown
    # provider ids in the schema, so it falls through to our
    # explicit 422 in the router.
    assert response.status_code == 422, response.text


def test_create_agent_rejects_extra_fields(client: TestClient) -> None:
    _login_as_admin(client)
    response = client.post(
        "/api/v1/agents",
        json={"name": "x", "config": _valid_config(), "sneaky": 1},
    )
    assert response.status_code == 422


def test_list_agents_empty_then_one(client: TestClient) -> None:
    _login_as_admin(client)
    # Empty.
    r1 = client.get("/api/v1/agents")
    assert r1.status_code == 200
    assert r1.json() == []

    # Create one.
    client.post("/api/v1/agents", json={"name": "A", "config": _valid_config()})
    r2 = client.get("/api/v1/agents")
    assert r2.status_code == 200
    assert len(r2.json()) == 1


def test_get_agent_includes_versions(client: TestClient) -> None:
    _login_as_admin(client)
    created = client.post(
        "/api/v1/agents", json={"name": "B", "config": _valid_config()}
    ).json()
    agent_id = created["id"]

    r = client.get(f"/api/v1/agents/{agent_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == agent_id
    assert len(body["versions"]) == 1


def test_new_version_creates_immutable_row(client: TestClient) -> None:
    _login_as_admin(client)
    created = client.post(
        "/api/v1/agents", json={"name": "V", "config": _valid_config()}
    ).json()
    agent_id = created["id"]
    v1_id = created["versions"][0]["id"]

    cfg2 = _valid_config()
    cfg2["system_prompt"] = "You are a stricter agent."
    r = client.post(
        f"/api/v1/agents/{agent_id}/versions",
        json={"config": cfg2, "change_note": "tighten tone"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["version_number"] == 2
    assert body["change_note"] == "tighten tone"
    assert body["id"] != v1_id

    # The original version is untouched.
    r_old = client.get(f"/api/v1/agents/{agent_id}/versions/{v1_id}")
    assert r_old.status_code == 200
    assert r_old.json()["config"]["system_prompt"] == "You are a helpful test agent."


def test_get_agent_404_for_unknown_id(client: TestClient) -> None:
    _login_as_admin(client)
    r = client.get("/api/v1/agents/does-not-exist")
    assert r.status_code == 404
