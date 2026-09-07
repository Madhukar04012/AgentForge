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

import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import {
  ApiError,
  ExecutionEvent,
  ExecutionStatus,
  ExecutionWithEvents,
  getExecution,
} from "../lib/api";

const TERMINAL_STATUSES: ReadonlySet<ExecutionStatus> = new Set([
  "completed",
  "failed",
  "cancelled",
]);

/** Execution detail — status, output, full event log. */
export function ExecutionDetailPage() {
  const { id = "" } = useParams<{ id: string }>();
  const [exec, setExec] = useState<ExecutionWithEvents | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  async function load() {
    try {
      const data = await getExecution(id);
      setExec(data);
      return data;
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setError("Execution not found.");
      } else {
        setError(err instanceof Error ? err.message : "Failed to load");
      }
      return null;
    }
  }

  useEffect(() => {
    let cancelled = false;
    async function start() {
      const data = await load();
      if (cancelled) return;
      if (data && !TERMINAL_STATUSES.has(data.status)) {
        // Poll once a second while the execution is in flight.
        pollRef.current = window.setInterval(async () => {
          const next = await load();
          if (next && TERMINAL_STATUSES.has(next.status) && pollRef.current) {
            window.clearInterval(pollRef.current);
            pollRef.current = null;
          }
        }, 1000);
      }
    }
    void start();
    return () => {
      cancelled = true;
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  if (!exec) {
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
          <h1 className="text-2xl font-semibold tracking-tight">Execution</h1>
          <p className="font-mono text-xs text-muted">{exec.id}</p>
        </div>
        <StatusBadge status={exec.status} />
      </header>

      <Card title="Input">
        <pre className="whitespace-pre-wrap font-mono text-sm">{exec.input}</pre>
      </Card>

      {exec.output ? (
        <Card title="Output">
          <pre className="whitespace-pre-wrap font-mono text-sm">
            {exec.output}
          </pre>
        </Card>
      ) : null}

      {exec.error ? (
        <Card title="Error">
          <pre className="whitespace-pre-wrap font-mono text-sm text-danger">
            {exec.error}
          </pre>
        </Card>
      ) : null}

      <Card title={`Event log (${exec.events.length})`}>
        {exec.events.length === 0 ? (
          <p className="text-sm text-muted">
            No events yet. The execution may still be queued — start the worker
            process to drive it forward.
          </p>
        ) : (
          <ol className="space-y-1 text-sm">
            {exec.events.map((ev) => (
              <EventRow key={ev.id} event={ev} />
            ))}
          </ol>
        )}
      </Card>

      <Card title="Metadata">
        <dl className="grid grid-cols-2 gap-2 text-sm">
          <dt className="text-muted">Agent</dt>
          <dd className="font-mono text-xs">{exec.agent_id}</dd>
          <dt className="text-muted">Version</dt>
          <dd className="font-mono text-xs">{exec.agent_version_id}</dd>
          <dt className="text-muted">Queued</dt>
          <dd>{new Date(exec.queued_at).toLocaleString()}</dd>
          {exec.started_at ? (
            <>
              <dt className="text-muted">Started</dt>
              <dd>{new Date(exec.started_at).toLocaleString()}</dd>
            </>
          ) : null}
          {exec.completed_at ? (
            <>
              <dt className="text-muted">Completed</dt>
              <dd>{new Date(exec.completed_at).toLocaleString()}</dd>
            </>
          ) : null}
          {exec.latency_ms !== null ? (
            <>
              <dt className="text-muted">Latency</dt>
              <dd>{exec.latency_ms} ms</dd>
            </>
          ) : null}
          {exec.tokens_in !== null ? (
            <>
              <dt className="text-muted">Tokens in / out</dt>
              <dd>
                {exec.tokens_in} / {exec.tokens_out ?? "?"}
              </dd>
            </>
          ) : null}
        </dl>
      </Card>

      <div>
        <Link to={`/agents/${exec.agent_id}`}>
          <Button variant="ghost">Back to agent</Button>
        </Link>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: ExecutionStatus }) {
  const color =
    status === "completed"
      ? "bg-green-600"
      : status === "failed"
        ? "bg-danger"
        : status === "running"
          ? "bg-accent"
          : status === "cancelled"
            ? "bg-muted"
            : "bg-yellow-600";
  return (
    <span
      className={`rounded px-2 py-1 text-xs font-medium uppercase tracking-wide text-white ${color}`}
    >
      {status}
    </span>
  );
}

function EventRow({ event }: { event: ExecutionEvent }) {
  return (
    <li className="rounded border border-border bg-surface px-2 py-1">
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs text-muted">
          #{event.sequence} {event.event_type}
        </span>
        <span className="text-xs text-muted">
          {new Date(event.occurred_at).toLocaleTimeString()}
        </span>
      </div>
      {event.payload ? (
        <pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap break-words font-mono text-xs text-muted">
          {JSON.stringify(event.payload, null, 2)}
        </pre>
      ) : null}
    </li>
  );
}
