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
import { Link, useNavigate, useParams } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import {
  AgentVersion,
  ApiError,
  createExecution,
  getAgent,
} from "../lib/api";

/** Run page — pick a version, write a prompt, fire off an execution. */
export function RunAgentPage() {
  const { id = "" } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [versions, setVersions] = useState<AgentVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<string>("");
  const [prompt, setPrompt] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const agent = await getAgent(id);
        if (cancelled) return;
        setVersions(agent.versions);
        setSelectedVersion(agent.current_version_id ?? agent.versions[0]?.id ?? "");
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load agent");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [id]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedVersion) {
      setError("No version selected");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const execution = await createExecution({
        agent_id: id,
        agent_version_id: selectedVersion,
        input: prompt,
      });
      navigate(`/executions/${execution.id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err instanceof Error ? err.message : "Failed to start execution");
      }
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="mx-auto max-w-3xl p-8">
        <Card>
          <p className="text-sm text-muted">Loading…</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 p-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Run agent</h1>
        <p className="text-muted">
          Select an immutable version to run. The runtime always executes
          against the exact version you pick.
        </p>
      </header>

      {error ? (
        <Card>
          <p className="text-sm text-danger" role="alert">
            {error}
          </p>
        </Card>
      ) : null}

      <form onSubmit={onSubmit} className="space-y-4">
        <Card title="Version">
          {versions.length === 0 ? (
            <p className="text-sm text-muted">No versions available.</p>
          ) : (
            <div className="space-y-2">
              {versions.map((v) => (
                <label key={v.id} className="flex items-start gap-2 text-sm">
                  <input
                    type="radio"
                    name="version"
                    value={v.id}
                    checked={selectedVersion === v.id}
                    onChange={() => setSelectedVersion(v.id)}
                    className="mt-1"
                  />
                  <span>
                    v{v.version_number} —{" "}
                    <span className="font-mono text-xs">
                      {v.config.model_provider}/{v.config.model_name}
                    </span>
                    {v.change_note ? (
                      <span className="ml-2 text-muted">— {v.change_note}</span>
                    ) : null}
                  </span>
                </label>
              ))}
            </div>
          )}
        </Card>

        <Card title="Prompt">
          <textarea
            required
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={6}
            placeholder="Write the user input here…"
            className="block w-full rounded-md border border-border bg-surface px-2 py-1.5 text-sm"
          />
        </Card>

        <div className="flex justify-end gap-2">
          <Link to={`/agents/${id}`}>
            <Button variant="ghost" type="button">
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            disabled={submitting || !prompt.trim() || !selectedVersion}
          >
            {submitting ? "Starting…" : "Start execution"}
          </Button>
        </div>
      </form>
    </div>
  );
}
