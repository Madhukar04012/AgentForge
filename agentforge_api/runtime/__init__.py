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

"""Runtime bridge: AgentVersion → provider → Execution.

The :func:`run_execution` function in this package is the
**single** entry point the Arq worker uses to execute a queued
:class:`Execution`. It:

  1. Loads the immutable :class:`AgentVersion` row.
  2. Validates the version's JSON config against the Pydantic
     :class:`AgentVersionConfig` schema.
  3. Resolves the configured :class:`ModelProvider` from the
     registry — failing with :class:`ProviderNotConfigured` if the
     provider id is unknown or its credentials are missing.
  4. Iterates the provider's :class:`ProviderStreamEvent` stream,
     persisting one :class:`ExecutionEvent` row per event with a
     monotonic ``sequence`` number.
  5. On completion, updates the parent :class:`Execution` row with
     the final output, token counts, latency, and ``completed``
     status. On failure (including provider not configured), the
     Execution is marked ``failed`` and the error is stored.
"""

from __future__ import annotations

from .bridge import (
    RunOutcome,
    run_execution,
)

__all__ = [
    "RunOutcome",
    "run_execution",
]
