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

"""Starlette middleware: request-ID and demo-mode banner.

* :class:`RequestIDMiddleware` — assigns a UUID to every request and
  echoes it as ``X-Request-ID``. Clients can pass their own ID via
  the same header for end-to-end tracing.
* :class:`DemoModeMiddleware` — when ``enabled=True``:

    1. On every incoming request, checks for the demo cookie
       (name from ``Settings.demo_cookie_name``) and, if present
       and non-empty, sets ``request.state.is_demo = True`` so the
       downstream dependency :func:`get_optional_user` can
       authenticate the request as the bootstrap admin.
    2. After the response, attaches ``X-Demo-Mode: 1`` if the
       request was a demo request. This lets the web app render a
       "Demo" banner.

Demo-mode is a Phase 1 affordance: a recruiter hits
``POST /api/v1/demo/session`` to mint a short-lived cookie, then
exercises the rest of the API as the bootstrap admin user without
having to sign up. The middleware is what makes the cookie
"sticky" — once issued, every subsequent request is treated as a
demo request until the cookie expires.
"""

from __future__ import annotations

import uuid
from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


REQUEST_ID_HEADER = "X-Request-ID"
DEMO_MODE_HEADER = "X-Demo-Mode"


def mark_demo_request(request: Request) -> None:
    """Mark a request as having been issued by a demo session.

    Called by the ``/api/v1/demo/session`` endpoint. The middleware
    also sets this flag automatically on every subsequent request
    that carries the demo cookie.
    """
    request.state.is_demo = True


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Stamp every request/response with a UUID request ID."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class DemoModeMiddleware(BaseHTTPMiddleware):
    """Recognize the demo cookie and attach ``X-Demo-Mode`` to responses."""

    def __init__(
        self,
        app,
        enabled: bool = True,
        cookie_name: str = "agentforge_demo",
    ) -> None:
        super().__init__(app)
        self.enabled = enabled
        self.cookie_name = cookie_name

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if self.enabled and not getattr(request.state, "is_demo", False):
            cookie_value = request.cookies.get(self.cookie_name)
            if cookie_value:
                request.state.is_demo = True
        response = await call_next(request)
        if self.enabled and getattr(request.state, "is_demo", False):
            response.headers[DEMO_MODE_HEADER] = "1"
        return response
