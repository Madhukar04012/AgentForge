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

"""HTTP router registry.

A single :data:`api_v1_router` aggregates every router. Phase 1
shipped ``health``, ``auth``, ``me``, and ``demo``; Phase 2 adds
``agents`` and ``executions``.
"""

from __future__ import annotations

from fastapi import APIRouter

from .agents import router as agents_router
from .auth import router as auth_router
from .demo import router as demo_router
from .executions import router as executions_router
from .health import router as health_router
from .me import router as me_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(me_router)
api_v1_router.include_router(demo_router)
api_v1_router.include_router(agents_router)
api_v1_router.include_router(executions_router)


__all__ = ["api_v1_router"]
