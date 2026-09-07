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

/**
 * Tiny fetch wrapper that:
 *   * always sends/receives JSON
 *   * sends cookies (so the session cookie travels)
 *   * surfaces non-2xx responses as thrown errors with a useful message
 *
 * The Vite dev server proxies `/api` to the FastAPI server, so this
 * works in dev and in production where the SPA is served behind the
 * same origin.
 */

export class ApiError extends Error {
  status: number;
  body: unknown;
  constructor(status: number, body: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const init: RequestInit = {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  };
  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }
  const response = await fetch(path, init);
  const text = await response.text();
  let parsed: unknown = null;
  if (text) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }
  if (!response.ok) {
    const detail =
      parsed && typeof parsed === "object" && parsed !== null && "detail" in parsed
        ? String((parsed as { detail: unknown }).detail)
        : `${method} ${path} failed (${response.status})`;
    throw new ApiError(response.status, parsed, detail);
  }
  return parsed as T;
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>("GET", path);
}

export function apiPost<T, B = unknown>(path: string, body: B): Promise<T> {
  return request<T>("POST", path, body);
}

export function apiDelete<T>(path: string): Promise<T> {
  return request<T>("DELETE", path);
}

// ---------------------------------------------------------------------------
// Domain types — Phase 2.
// ---------------------------------------------------------------------------

export type ExecutionStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface AgentVersion {
  id: string;
  agent_id: string;
  version_number: number;
  config: AgentVersionConfig;
  change_note: string | null;
  created_at: string;
}

export interface Agent {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  current_version_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AgentWithVersions extends Agent {
  versions: AgentVersion[];
}

export interface AgentVersionConfig {
  model_provider: string;
  model_name: string;
  system_prompt: string;
  tools: { type: string; name: string }[];
  generation_config: {
    temperature?: number;
    top_p?: number;
    max_output_tokens?: number;
  };
}

export interface Execution {
  id: string;
  workspace_id: string;
  agent_id: string;
  agent_version_id: string;
  status: ExecutionStatus;
  input: string;
  output: string | null;
  error: string | null;
  tokens_in: number | null;
  tokens_out: number | null;
  cost_usd: number | null;
  latency_ms: number | null;
  queued_at: string;
  started_at: string | null;
  completed_at: string | null;
  triggered_by_id: string | null;
}

export interface ExecutionEvent {
  id: string;
  sequence: number;
  event_type: string;
  payload: Record<string, unknown> | null;
  occurred_at: string;
}

export interface ExecutionWithEvents extends Execution {
  events: ExecutionEvent[];
}

// ---------------------------------------------------------------------------
// High-level helpers.
// ---------------------------------------------------------------------------

export function listAgents(): Promise<Agent[]> {
  return apiGet<Agent[]>("/api/v1/agents");
}

export function getAgent(id: string): Promise<AgentWithVersions> {
  return apiGet<AgentWithVersions>(`/api/v1/agents/${id}`);
}

export function createAgent(input: {
  name: string;
  description?: string;
  config: AgentVersionConfig;
  change_note?: string;
}): Promise<AgentWithVersions> {
  return apiPost<AgentWithVersions, typeof input>("/api/v1/agents", input);
}

export function createAgentVersion(
  agentId: string,
  input: { config: AgentVersionConfig; change_note?: string },
): Promise<AgentVersion> {
  return apiPost<AgentVersion, typeof input>(
    `/api/v1/agents/${agentId}/versions`,
    input,
  );
}

export function listExecutions(): Promise<Execution[]> {
  return apiGet<Execution[]>("/api/v1/executions");
}

export function getExecution(id: string): Promise<ExecutionWithEvents> {
  return apiGet<ExecutionWithEvents>(`/api/v1/executions/${id}`);
}

export function createExecution(input: {
  agent_id: string;
  agent_version_id: string;
  input: string;
}): Promise<Execution> {
  return apiPost<Execution, typeof input>("/api/v1/executions", input);
}

