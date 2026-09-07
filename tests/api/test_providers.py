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

"""Provider registry + stub behavior tests."""

from __future__ import annotations

import pytest

from agentforge_api.providers import (
    GoogleProvider,
    ProviderNotConfigured,
    get_provider,
    registered_provider_ids,
)
from agentforge_api.providers.base import ProviderRequest


def test_registry_contains_expected_providers() -> None:
    ids = set(registered_provider_ids())
    assert {"google", "openai", "anthropic", "openrouter", "ollama"} <= ids


def test_get_provider_unknown_raises() -> None:
    with pytest.raises(ProviderNotConfigured) as exc:
        get_provider("nope-not-a-real-provider")
    assert "Unknown" in str(exc.value)


@pytest.mark.parametrize(
    "stub_id", ["openai", "anthropic", "openrouter", "ollama"]
)
def test_stubs_always_raise(stub_id: str) -> None:
    """Stubs must NEVER produce a fake response."""
    request = ProviderRequest(
        agent_version_id="v-1",
        model_provider=stub_id,
        model_name="some-model",
        system_prompt="you are a test",
        user_input="hello",
    )
    with pytest.raises(ProviderNotConfigured) as exc:
        # ``get_provider`` returns a stub instance; calling invoke
        # is what raises.
        provider = get_provider(stub_id) if get_provider.__class__ else None
        if provider is None:
            # is_configured() is False for stubs, so get_provider
            # itself raises. Verify that path.
            from agentforge_api.providers import get_provider as _gp

            with pytest.raises(ProviderNotConfigured):
                _gp(stub_id)
        else:  # pragma: no cover - defensive
            list(provider.invoke(request))
    assert stub_id in str(exc.value)


def test_stub_is_configured_is_false() -> None:
    """All four stubs must report is_configured() == False."""
    from agentforge_api.providers.stubs import (
        AnthropicProvider,
        OllamaProvider,
        OpenAIProvider,
        OpenRouterProvider,
    )

    for cls in (OpenAIProvider, AnthropicProvider, OpenRouterProvider, OllamaProvider):
        assert cls.is_configured() is False


def test_google_provider_is_configured_only_when_key_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert GoogleProvider.is_configured() is False

    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    assert GoogleProvider.is_configured() is True
    # Gemini takes precedence in the order we read; setting it
    # should also work.
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-2")
    assert GoogleProvider.is_configured() is True
