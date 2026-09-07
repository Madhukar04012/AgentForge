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

"""Model provider abstraction.

A :class:`ModelProvider` translates an :class:`AgentVersion`'s
``config`` (system_prompt, model name, generation params, …) plus a
user input string into a stream of runtime events that the worker
persists as :class:`agentforge_api.models.execution.ExecutionEvent`
rows.

The Phase 2 vertical slice ships:

  * :class:`GoogleProvider` — **real** integration with Google ADK's
    ``Gemini`` model and ``LlmAgent`` runtime. The actual model call
    is performed by ADK; this provider just configures the ADK
    objects and translates ADK events into our event vocabulary.
  * Four stub providers (:class:`OpenAIProvider`,
    :class:`AnthropicProvider`, :class:`OpenRouterProvider`,
    :class:`OllamaProvider`) that explicitly raise
    :class:`ProviderNotConfigured` so the caller can report a clear
    error to the end user. **They do not fake a model response.**

No provider implementation here ever fabricates model output.
If credentials are missing or a provider is not yet integrated, the
provider raises an explicit exception and the execution is marked
``failed`` with a descriptive message.
"""

from __future__ import annotations

# Importing the submodules is what triggers @register_provider. The
# order matters: ``base`` first (defines the registry), then the
# real Google provider, then the stubs.
from . import base  # noqa: F401
from . import google  # noqa: F401
from . import stubs  # noqa: F401

from .base import (
    ModelProvider,
    ProviderError,
    ProviderInvocationError,
    ProviderNotConfigured,
    ProviderRequest,
    ProviderResponse,
    ProviderStreamEvent,
    get_provider,
    register_provider,
    registered_provider_ids,
)
from .google import GoogleProvider
from .stubs import (
    AnthropicProvider,
    OllamaProvider,
    OpenAIProvider,
    OpenRouterProvider,
)

__all__ = [
    "AnthropicProvider",
    "GoogleProvider",
    "ModelProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    "ProviderError",
    "ProviderInvocationError",
    "ProviderNotConfigured",
    "ProviderRequest",
    "ProviderResponse",
    "ProviderStreamEvent",
    "get_provider",
    "register_provider",
    "registered_provider_ids",
]
