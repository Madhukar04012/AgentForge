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

"""Auth — login, logout, /me."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_login_rejects_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@agentforge.example.com", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_rejects_missing_fields(client: TestClient) -> None:
    response = client.post("/api/v1/auth/login", json={})
    assert response.status_code == 422


def test_login_succeeds_with_seeded_admin(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@agentforge.example.com", "password": "not-a-real-password"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0
    # The session cookie is set on the response.
    set_cookies = response.headers.get("set-cookie", "")
    assert "agentforge_session" in set_cookies


def test_logout_clears_cookie(client: TestClient) -> None:
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 204
    set_cookies = response.headers.get("set-cookie", "")
    # The delete-cookie header will mention the cookie name even if
    # the body is empty — we only care that the name is present.
    assert "agentforge_session" in set_cookies


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/me")
    assert response.status_code == 401
