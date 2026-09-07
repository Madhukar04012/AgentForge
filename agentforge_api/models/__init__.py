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

"""SQLAlchemy ORM models.

Phase 1 shipped the tables required for the demo flow and the
placeholder auth flow:
  * :mod:`agentforge_api.models.workspace` — ``User``,
    ``Workspace``, ``WorkspaceMember``.
  * :mod:`agentforge_api.models.audit` — ``AuditLog``.
  * :mod:`agentforge_api.models.demo` — ``DemoSession``.

Phase 2 adds the tables required for the real agent runtime
vertical slice:
  * :mod:`agentforge_api.models.agent` — ``Agent``,
    ``AgentVersion``.
  * :mod:`agentforge_api.models.execution` — ``Execution``,
    ``ExecutionEvent``.

All other tables (``workflows``, ``evaluation_*``, ``deployments``,
``api_keys``, ``integrations``) land in their respective phases per
the Phase 1 audit document.
"""

from __future__ import annotations

from .agent import Agent, AgentVersion
from .audit import AuditLog
from .demo import DemoSession
from .execution import Execution, ExecutionEvent, ExecutionStatus
from .workspace import User, Workspace, WorkspaceMember, WorkspaceRole

__all__ = [
    "Agent",
    "AgentVersion",
    "AuditLog",
    "DemoSession",
    "Execution",
    "ExecutionEvent",
    "ExecutionStatus",
    "User",
    "Workspace",
    "WorkspaceMember",
    "WorkspaceRole",
]
