// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import {
  AgentVersionConfig,
  apiPost,
  createAgent,
  ApiError,
} from "../lib/api";

interface ProviderOption {
  id: string;
  label: string;
  configured: boolean;
  default_model: string;
}

const FALLBACK_PROVIDERS: ProviderOption[] = [
  {
    id: "google",
    label: "Google (Gemini, via ADK)",
    configured: true,
    default_model: "gemini-2.0-flash",
  },
  {
    id: "openai",
    label: "OpenAI (not yet integrated)",
    configured: false,
    default_model: "gpt-4o-mini",
  },
  {
    id: "anthropic",
    label: "Anthropic (not yet integrated)",
    configured: false,
    default_model: "claude-3-5-sonnet-latest",
  },
  {
    id: "openrouter",
    label: "OpenRouter (not yet integrated)",
    configured: false,
    default_model: "openrouter/auto",
  },
  {
    id: "ollama",
    label: "Ollama (not yet integrated)",
    configured: false,
    default_model: "llama3.1",
  },
];

/** Form to create a new agent (and its initial version). */
export function NewAgentPage() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [provider, setProvider] = useState<string>("google");
  const [model, setModel] = useState<string>("gemini-2.0-flash");
  const [systemPrompt, setSystemPrompt] = useState(
    "You are a helpful assistant.",
  );
  const [temperature, setTemperature] = useState(0.2);
  const [maxTokens, setMaxTokens] = useState(512);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [providers, setProviders] = useState<ProviderOption[]>(FALLBACK_PROVIDERS);

  // Make sure we have a session before allowing submit.
  useEffect(() => {
    void apiPost<unknown, Record<string, never>>(
      "/api/v1/demo/session",
      {},
    ).catch(() => undefined);
  }, []);

  // We don't expose a /providers endpoint in Phase 2; the list is
  // hard-coded client-side. The server is the source of truth and
  // will reject unknown provider ids.

  const selectedProvider = providers.find((p) => p.id === provider);

  function onProviderChange(next: string) {
    setProvider(next);
    const opt = providers.find((p) => p.id === next);
    if (opt) setModel(opt.default_model);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    const config: AgentVersionConfig = {
      model_provider: provider,
      model_name: model,
      system_prompt: systemPrompt,
      tools: [],
      generation_config: {
        temperature,
        max_output_tokens: maxTokens,
      },
    };
    try {
      const agent = await createAgent({
        name: name.trim(),
        description: description.trim() || undefined,
        config,
        change_note: "Initial version",
      });
      navigate(`/agents/${agent.id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : "Failed to create agent");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 p-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">New agent</h1>
        <p className="text-muted">
          A version is created automatically. You can edit it later to start a
          new version.
        </p>
      </header>

      <form onSubmit={onSubmit} className="space-y-4">
        <Card>
          <div className="space-y-3">
            <label className="block text-sm">
              <span className="font-medium">Name</span>
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Compressor"
                className="mt-1 block w-full rounded-md border border-border bg-surface px-2 py-1.5 text-sm"
              />
            </label>
            <label className="block text-sm">
              <span className="font-medium">Description (optional)</span>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="mt-1 block w-full rounded-md border border-border bg-surface px-2 py-1.5 text-sm"
              />
            </label>
          </div>
        </Card>

        <Card title="Model">
          <div className="space-y-3">
            <label className="block text-sm">
              <span className="font-medium">Provider</span>
              <select
                value={provider}
                onChange={(e) => onProviderChange(e.target.value)}
                className="mt-1 block w-full rounded-md border border-border bg-surface px-2 py-1.5 text-sm"
              >
                {providers.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.label}
                  </option>
                ))}
              </select>
              {selectedProvider && !selectedProvider.configured ? (
                <p className="mt-1 text-xs text-warning">
                  This provider is not yet integrated. Saving the agent will
                  succeed, but executions will fail until the provider ships.
                </p>
              ) : null}
            </label>
            <label className="block text-sm">
              <span className="font-medium">Model</span>
              <input
                required
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="mt-1 block w-full rounded-md border border-border bg-surface px-2 py-1.5 text-sm font-mono"
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="block text-sm">
                <span className="font-medium">Temperature</span>
                <input
                  type="number"
                  step="0.05"
                  min={0}
                  max={2}
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                  className="mt-1 block w-full rounded-md border border-border bg-surface px-2 py-1.5 text-sm"
                />
              </label>
              <label className="block text-sm">
                <span className="font-medium">Max output tokens</span>
                <input
                  type="number"
                  min={1}
                  max={100000}
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(Number(e.target.value))}
                  className="mt-1 block w-full rounded-md border border-border bg-surface px-2 py-1.5 text-sm"
                />
              </label>
            </div>
          </div>
        </Card>

        <Card title="System prompt">
          <textarea
            required
            value={systemPrompt}
            onChange={(e) => setSystemPrompt(e.target.value)}
            rows={6}
            className="block w-full rounded-md border border-border bg-surface px-2 py-1.5 font-mono text-sm"
          />
        </Card>

        {error ? (
          <Card>
            <p className="text-sm text-danger" role="alert">
              {error}
            </p>
          </Card>
        ) : null}

        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate("/agents")}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={submitting || !name.trim()}>
            {submitting ? "Creating…" : "Create agent"}
          </Button>
        </div>
      </form>
    </div>
  );
}
