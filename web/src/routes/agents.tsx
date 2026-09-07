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
import { Link } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Agent, listAgents, ApiError, apiPost } from "../lib/api";

/** Agents list — the real Phase 2 landing surface. */
export function AgentsPage() {
  const [agents, setAgents] = useState<Agent[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [needsAuth, setNeedsAuth] = useState(false);

  async function ensureSession(): Promise<void> {
    // If we are not yet authenticated (no demo cookie), mint one.
    // This is a Phase-1 / Phase-2 affordance: a recruiter can
    // click "Agents" and immediately get a working session.
    try {
      await apiPost<unknown, Record<string, never>>(
        "/api/v1/demo/session",
        {},
      );
    } catch {
      // The list call below will surface the real error.
    }
  }

  async function load(): Promise<void> {
    setError(null);
    try {
      const data = await listAgents();
      setAgents(data);
      setNeedsAuth(false);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        await ensureSession();
        try {
          const data = await listAgents();
          setAgents(data);
          setNeedsAuth(false);
          return;
        } catch (err2) {
          setError(err2 instanceof Error ? err2.message : "Failed to load");
          return;
        }
      }
      setError(err instanceof Error ? err.message : "Failed to load");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 p-8">
      <header className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Agents</h1>
          <p className="text-muted">
            Real, executable agents backed by the ADK runtime.
          </p>
        </div>
        <Link to="/agents/new">
          <Button>New agent</Button>
        </Link>
      </header>

      {error ? (
        <Card>
          <p className="text-sm text-danger" role="alert">
            {error}
          </p>
          <div className="mt-3">
            <Button onClick={load}>Retry</Button>
          </div>
        </Card>
      ) : null}

      {needsAuth ? (
        <Card>
          <p className="text-sm text-muted">
            Sign in or start a demo session to view your agents.
          </p>
        </Card>
      ) : null}

      {agents === null ? (
        <Card>
          <p className="text-sm text-muted">Loading…</p>
        </Card>
      ) : agents.length === 0 ? (
        <Card title="No agents yet">
          <p className="text-sm text-muted">
            Create your first agent to start running real model invocations.
          </p>
          <div className="mt-3">
            <Link to="/agents/new">
              <Button>New agent</Button>
            </Link>
          </div>
        </Card>
      ) : (
        <ul className="space-y-3">
          {agents.map((a) => (
            <li key={a.id}>
              <Card>
                <div className="flex items-center justify-between">
                  <div>
                    <Link
                      to={`/agents/${a.id}`}
                      className="text-lg font-medium hover:underline"
                    >
                      {a.name}
                    </Link>
                    {a.description ? (
                      <p className="text-sm text-muted">{a.description}</p>
                    ) : null}
                  </div>
                  <div className="flex gap-2">
                    <Link to={`/agents/${a.id}/run`}>
                      <Button>Run</Button>
                    </Link>
                    <Link to={`/agents/${a.id}`}>
                      <Button variant="ghost">Details</Button>
                    </Link>
                  </div>
                </div>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
