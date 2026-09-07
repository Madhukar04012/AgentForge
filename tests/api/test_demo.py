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

"""Recruiter demo endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_demo_session(client: TestClient) -> None:
    response = client.post("/api/v1/demo/session", json={})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["session_id"]
    assert body["demo_mode"] is True
    assert body["expires_at"]
    # The demo cookie is set.
    set_cookies = response.headers.get("set-cookie", "")
    assert "agentforge_demo" in set_cookies


def test_demo_session_marks_response(client: TestClient) -> None:
    response = client.post("/api/v1/demo/session", json={})
    assert response.status_code == 201
    # The middleware writes X-Demo-Mode: 1 to the response.
    assert response.headers.get("X-Demo-Mode") == "1"


def test_read_demo_project_returns_placeholder(client: TestClient) -> None:
    response = client.get("/api/v1/demo/project")
    assert response.status_code == 200
    body = response.json()
    assert body["title"]
    assert body["summary"]
    assert isinstance(body["agents"], list)
    assert "Phase 14" in body["message"]
