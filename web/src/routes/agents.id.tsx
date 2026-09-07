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
import { Link, useParams } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import {
  AgentVersion,
  AgentWithVersions,
  getAgent,
  ApiError,
} from "../lib/api";

/** Agent detail page — shows versions + new-version form. */
export function AgentDetailPage() {
  const { id = "" } = useParams<{ id: string }>();
  const [agent, setAgent] = useState<AgentWithVersions | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const data = await getAgent(id);
      setAgent(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setError("Agent not found.");
      } else {
        setError(err instanceof Error ? err.message : "Failed to load");
      }
    }
  }

  useEffect(() => {
    void load();
  }, [id]);

  if (error) {
    return (
      <div className="mx-auto max-w-3xl p-8">
        <Card>
          <p className="text-sm text-danger" role="alert">
            {error}
          </p>
          <div className="mt-3">
            <Link to="/agents">
              <Button variant="ghost">Back to agents</Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  if (!agent) {
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
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{agent.name}</h1>
          {agent.description ? (
            <p className="text-muted">{agent.description}</p>
          ) : null}
          <p className="font-mono text-xs text-muted">
            {agent.id} — current version{" "}
            {agent.current_version_id ? agent.current_version_id.slice(0, 8) : "(none)"}
          </p>
        </div>
        <div className="flex gap-2">
          <Link to={`/agents/${agent.id}/run`}>
            <Button>Run</Button>
          </Link>
        </div>
      </header>

      <Card title={`Versions (${agent.versions.length})`}>
        {agent.versions.length === 0 ? (
          <p className="text-sm text-muted">No versions yet.</p>
        ) : (
          <ul className="space-y-3">
            {agent.versions.map((v) => (
              <VersionRow key={v.id} version={v} currentVersionId={agent.current_version_id} />
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function VersionRow({
  version,
  currentVersionId,
}: {
  version: AgentVersion;
  currentVersionId: string | null;
}) {
  const isCurrent = version.id === currentVersionId;
  return (
    <li>
      <div
        className={
          "rounded-md border p-3 " +
          (isCurrent ? "border-accent bg-accent/5" : "border-border bg-surface")
        }
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">
              v{version.version_number}
              {isCurrent ? (
                <span className="ml-2 rounded bg-accent px-1.5 py-0.5 text-xs text-white">
                  current
                </span>
              ) : null}
            </p>
            <p className="font-mono text-xs text-muted">
              {version.config.model_provider}/{version.config.model_name}
            </p>
            {version.change_note ? (
              <p className="mt-1 text-sm text-muted">{version.change_note}</p>
            ) : null}
          </div>
        </div>
        {version.config.system_prompt ? (
          <details className="mt-2 text-sm">
            <summary className="cursor-pointer text-muted">System prompt</summary>
            <pre className="mt-1 whitespace-pre-wrap rounded bg-surface p-2 font-mono text-xs">
              {version.config.system_prompt}
            </pre>
          </details>
        ) : null}
      </div>
    </li>
  );
}
