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

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { apiGet, apiPost } from "../lib/api";

interface DemoProject {
  title: string;
  summary: string;
  agents: string[];
  workflow: string | null;
  message: string;
}

interface DemoSession {
  session_id: string;
  expires_at: string;
  demo_mode: boolean;
}

/** Recruiter demo entry — issues a session, then loads the seed project. */
export function DemoPage() {
  const [project, setProject] = useState<DemoProject | null>(null);
  const [session, setSession] = useState<DemoSession | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function startDemo() {
    setError(null);
    try {
      const s = await apiPost<DemoSession, Record<string, never>>(
        "/api/v1/demo/session",
        {},
      );
      setSession(s);
      const p = await apiGet<DemoProject>("/api/v1/demo/project");
      setProject(p);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo failed");
    }
  }

  useEffect(() => {
    // Auto-start on mount so the recruiter flow is one click away.
    void startDemo();
  }, []);

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 p-8">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          Recruiter demo
        </h1>
        <p className="text-muted">
          A pre-seeded AgentForge project — no API key required.
        </p>
      </header>

      {error ? (
        <Card>
          <p className="text-sm text-danger" role="alert">
            {error}
          </p>
          <div className="mt-3">
            <Button onClick={startDemo}>Retry</Button>
          </div>
        </Card>
      ) : null}

      {session ? (
        <Card title="Session" subtitle="Anonymous, short-lived.">
          <p className="font-mono text-xs text-muted">
            {session.session_id} — expires {session.expires_at}
          </p>
        </Card>
      ) : null}

      {project ? (
        <Card title={project.title} subtitle="Seed project">
          <p className="text-sm">{project.summary}</p>
          <div className="mt-3 text-sm">
            <p className="font-medium">Agents</p>
            <ul className="ml-5 list-disc text-muted">
              {project.agents.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </div>
          {project.workflow ? (
            <p className="mt-3 text-sm text-muted">
              Workflow: <code>{project.workflow}</code>
            </p>
          ) : null}
          <p className="mt-3 text-xs text-warning">{project.message}</p>
        </Card>
      ) : !error ? (
        <Card>
          <p className="text-sm text-muted">Loading demo…</p>
        </Card>
      ) : null}
    </div>
  );
}
