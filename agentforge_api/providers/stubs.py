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

"""Not-yet-integrated provider stubs.

Per the Phase 2 directive: *do not implement every provider yet if
doing so would create fake or incomplete integrations*. These
classes register under their stable provider ids so the API can
list them in the UI, but every call to :meth:`invoke` raises
:class:`ProviderNotConfigured` with a clear, user-facing message.

When we add a real implementation for one of these, the new
provider will register under the same id and the stub will be
removed. The id stability is what matters — agent versions saved
today must continue to load tomorrow.
"""

from __future__ import annotations

from typing import Iterator

from .base import (
    ModelProvider,
    ProviderNotConfigured,
    ProviderRequest,
    ProviderStreamEvent,
    register_provider,
)


def _stub(name: str, hint: str) -> type[ModelProvider]:
    """Build a :class:`ModelProvider` subclass that always refuses.

    Args:
        name: The provider id (e.g. ``"openai"``).
        hint: A short, user-facing sentence explaining how to
            enable the provider (e.g. ``"Set OPENAI_API_KEY and
            install openai>=1.40"``).
    """

    def invoke(
        self, request: ProviderRequest
    ) -> Iterator[ProviderStreamEvent]:
        raise ProviderNotConfigured(
            f"Model provider {name!r} is not yet implemented in "
            f"AgentForge. {hint}"
        )
        # Make the type checker happy: the body never runs but the
        # generator signature must be present.
        yield ProviderStreamEvent(kind="done")  # pragma: no cover

    @classmethod
    def is_configured(cls) -> bool:
        return False

    attrs = {
        "name": name,
        "__doc__": (
            f"Stub for the {name!r} provider. Always raises "
            f"ProviderNotConfigured; the real integration has not "
            f"been added yet."
        ),
        "invoke": invoke,
        "is_configured": is_configured,
    }
    return type(f"{name.capitalize()}ProviderStub", (ModelProvider,), attrs)


# Register the four not-yet-integrated providers. The ids are
# stable; a future phase will replace each stub with a real
# implementation under the same id.
OpenAIProvider = register_provider(
    _stub(
        "openai",
        "A future phase will integrate the OpenAI Python SDK.",
    )
)
AnthropicProvider = register_provider(
    _stub(
        "anthropic",
        "A future phase will integrate the Anthropic Python SDK.",
    )
)
OpenRouterProvider = register_provider(
    _stub(
        "openrouter",
        "A future phase will integrate OpenRouter via the OpenAI-compatible API.",
    )
)
OllamaProvider = register_provider(
    _stub(
        "ollama",
        "A future phase will integrate Ollama over its local HTTP API.",
    )
)

__all__ = [
    "AnthropicProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
]
