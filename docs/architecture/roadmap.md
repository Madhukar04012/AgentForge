# AgentForge Implementation Roadmap

> **Phase 1 is the current phase.** Each row has a goal, the phase it
> depends on, and the definition of done (DoD). Phases are ordered so
> the recruiter demo and product shape come early; the full
> rationale is in `docs/architecture/architecture.md` and the audit
> report archived in project memory.

## Phase tracker

| Phase | Goal | Depends on | Status | DoD |
|-------|------|------------|--------|-----|
| 1 | **Foundation** — repo layout, monorepo, web/API skeletons, infra, demo route | — | ✅ in this PR | `docker compose up` brings up Postgres, Redis, API, Web; `/api/v1/health` returns 200; `/api/v1/demo/session` issues a cookie; the SPA shows a landing page and a "Try Demo" button. |
| 2 | **Agent Runtime API** — refactor eval/deploy/scaffold into callable libraries; CRUD + version APIs | 1 | not started | `agentforge_api.services.eval` wraps the existing `google.agents.cli.eval` modules; `/api/v1/agents` endpoints pass e2e. |
| 3 | **Model Provider Layer** — `ModelProvider` ABC + OpenAI/Anthropic/Google/Ollama/OpenRouter | 2 | not started | Six provider modules behind one ABC; integration tests with mocked responses. |
| 4 | **Workflow Engine** — engine, validation, persistence, executor | 2 | not started | DAG validator, sequential/parallel/conditional/loop nodes, persistence + replay. |
| 5 | **Web Workflow Builder** — React Flow + Monaco editors | 4 | not started | Drag-and-drop builder; saves a new immutable version on every change. |
| 6 | **Execution + Streaming** — executor, SSE, event log | 2,3,4 | not started | `/api/v1/executions` start + SSE stream; event log persists in `execution_events`. |
| 7 | **Observability** — spans, trace dashboard | 6 | not started | React Flow span tree on the execution detail page. |
| 8 | **Evaluation** — web eval lab; reuse `eval/*.py` | 2,3,6 | not started | Dataset CRUD, run config, results table, side-by-side compare. |
| 9 | **Failure Analysis** — classifier + UI | 7,8 | not started | `FailureCategory` enum, suggested-fix descriptors, trace annotation. |
| 10 | **Self-Correction + Versioning** — propose, eval-compare, promote | 2,8,9 | not started | "Propose" generates a candidate `agent_versions` row; "Promote" requires an eval pass. |
| 11 | **GitHub + Docker Sandbox** — OAuth, webhook, per-exec container | 2,6 | not started | GitHub OAuth app; per-execution Docker container with allowlisted egress. |
| 12 | **Deployment** — web deploy action + status | 2 | not started | "Deploy" dialog writes a `deployments` row; long-poll status. |
| 13 | **Authentication + Workspaces** — full multi-tenant auth | 1,2 | not started | Email/pw + OAuth, refresh-token rotation, RBAC, audit log writes. |
| 14 | **Recruiter Demo + Product Polish** — pre-seeded demo, screenshots, docs | 1,6,7,8 | not started | Recruiter reaches a populated trace detail page in ≤ 3 clicks / 10 s without sign-up. |
| 15 | **Production Hardening** — RBAC, audit, secrets, rate limits, perf, SSO | all | not started | Per-tenant rate limits, secret encryption, load test, SSO. |

## Phase 1 — Foundation (this PR)

### Files added
- `agentforge_api/` — 20 files (FastAPI app, settings, DB, auth stub,
  health, login/logout, demo, migrations).
- `web/` — 18 files (Vite + React + TS + Tailwind, three routes,
  Button + Card primitives, tests).
- `docker/` — 4 files (Dockerfile.api, Dockerfile.web, web.nginx.conf,
  docker-compose.yml).
- `docs/architecture/` — 2 files (architecture.md, roadmap.md).

### Files modified
- `README.md` — small "Web Platform" section appended.
- `RELEASE_NOTES.md` — small "Unreleased" section appended.
- `pyproject.toml` — created at the repo root (none existed
  previously) declaring `agentforge_api` and a `uv` workspace.

### Files *not* modified
- `src/google/agents/cli/` (the CLI)
- `src/agentforge/` (the parallel CLI source tree)
- `extensions/`, `skills/`, `docs/`
- Any template under `src/**/scaffold/`

### Verification
- `docker compose -f docker/docker-compose.yml up` brings up the
  stack.
- `curl http://localhost:8000/api/v1/health` → 200 `{"status":"ok"}`.
- `curl -X POST -i http://localhost:8000/api/v1/demo/session` → 201
  with `Set-Cookie: agentforge_demo=...`.
- `cd web && pnpm test` → green.
- `cd web && pnpm exec playwright test` → smoke green.
- `agentforge --version` / `agentforge --version` — unchanged (the
  CLI source was not touched).
