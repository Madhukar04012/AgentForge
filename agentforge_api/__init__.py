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

"""AgentForge web platform API.

This package is the FastAPI backend for the AgentForge web app. It is
intentionally additive: it sits alongside the existing
``google.agents.cli`` (CLI) and ``src/agentforge`` (CLI source tree)
packages and does not modify either.

Phase 1 ships only the skeleton — settings, DB, auth stub, health,
login/logout, and a placeholder recruiter-demo session endpoint. Real
business endpoints (agents, workflows, executions, evaluations,
deployments) arrive in later phases.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0-phase1"
