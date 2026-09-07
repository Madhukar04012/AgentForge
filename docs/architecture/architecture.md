# AgentForge Architecture

> **Phase 1.** This is the long-form design that Phase 1 implements. The
> source of truth is `docs/architecture/roadmap.md` for the phase
> tracker, and the audit report previously delivered in chat (also
> archived as the project memory note) for the full 19-section audit.
> This page is the slimmed, repo-anchored summary.

## What is AgentForge?

AgentForge is the web frontend for the existing
[`agentforge`](https://pypi.org/project/agentforge/)
foundation. The CLI (and its console script alias `agentforge`) is
unchanged. The web app is a thin FastAPI backend + React/Vite SPA that
wraps the CLI's eval flywheel, deploy targets, and ADK-backed agent
runtime in a browser experience.

## High-level topology

```
   ┌────────────────────────┐    ┌────────────────────────┐
   │   Web SPA (Vite/React) │    │   agentforge (CLI)     │
   └────────────┬───────────┘    └────────────────────────┘
                │ HTTPS
       ┌────────▼────────┐
       │  FastAPI (api)  │
       │  agentforge_api │
       └──┬──────────┬───┘
          │          │
     ┌────▼────┐ ┌────▼────┐
     │ Postgres│ │  Redis  │   (Phase 6+ for queue + pub/sub)
     └─────────┘ └─────────┘
```

## What Phase 1 ships

- **Backend (`agentforge_api/`)** — FastAPI app factory, settings via
  pydantic-settings, SQLAlchemy engine, JWT helpers, request-ID +
  demo-mode middleware, and the following endpoints:
  - `GET  /api/v1/health`
  - `POST /api/v1/auth/login` (placeholder email + password)
  - `POST /api/v1/auth/logout`
  - `GET  /api/v1/me`
  - `POST /api/v1/demo/session` (recruiter demo entry)
  - `GET  /api/v1/demo/project` (placeholder content)
- **ORM** — `User`, `Workspace`, `WorkspaceMember`, `AuditLog`,
  `DemoSession` tables. All other tables land in later phases per the
  audit document.
- **Migrations** — Alembic env + initial migration `0001_init`.
- **Web (`web/`)** — Vite + React + TypeScript + Tailwind. Three
  routes: `/`, `/login`, `/demo`. Button + Card primitives. Theme
  tokens for light + dark.
- **Docker (`docker/`)** — multi-stage images for the API and the
  web, plus a `docker-compose.yml` that wires Postgres, Redis, the
  API, and the web together for local dev.
- **Tests** — pytest for the API (health, auth, demo), Vitest for
  the Button component, Playwright smoke test for the landing page.

## What Phase 1 does *not* do

- It does not modify `src/google/agents/cli/`, `src/agentforge/`,
  `extensions/`, `skills/`, or any other existing CLI code.
- It does not introduce any new runtime dependency for the CLI.
- It does not ship business endpoints for agents, workflows,
  executions, evaluations, or deployments — those arrive in Phase 2+.
- It does not add a real auth UI polish, OAuth, MFA, or API keys —
  those arrive in Phase 13.
- It does not seed the demo project with real content — the
  `/api/v1/demo/project` endpoint returns a static placeholder until
  Phase 14.

## Reuse from the existing repo

Phase 1 deliberately does not import anything from the existing
`google.agents.cli` package. Later phases will; this is when the
"wrap, don't fork" strategy pays off. The modules we will call into
include:

- `google.agents.cli.eval.*` — the eval flywheel core.
- `google.agents.cli.deploy.*` — Cloud Run / GKE / Agent Runtime.
- `google.agents.cli.scaffold.utils.*` — language dispatch, lock
  handling, conditional files, name validation, upgrade 3-way merge.
- `google.agents.cli.scaffold.agents.adk.app.fast_api_app` — the
  ADK FastAPI app template.
- `google.agents.cli.extension.*` — extension discovery, vendoring,
  and trust gate.
- `google.agents.cli._runner` / `_tools` / `_output` / `_click` /
  `_experiments` / `_remote` / `_gcp_project` / `auth`.

These are listed in the audit report with rationale and the exact
reuse strategy for each.

## Security notes (Phase 1)

- Passwords are hashed with Argon2id.
- JWTs are signed with HS256 against a `Settings.jwt_secret`; the
  default is clearly marked as dev-only and refused by pydantic when
  shorter than 8 characters.
- Cookies are HTTP-only, `SameSite=Lax`, and `Secure` outside dev.
- CORS is a strict allowlist; no wildcard.
- The extension system's CWE-59, CWE-22, and redaction protections
  are preserved verbatim (we do not touch the relevant files).
- Demo sessions are server-issued cookies with a per-session UUID;
  no PII is collected.

## Repo layout after Phase 1

```
AgentForge/
├── agentforge_api/          # NEW — FastAPI backend
├── web/                     # NEW — Vite + React + TS SPA
├── docker/                  # NEW — API + web images, compose, nginx
├── docs/architecture/       # NEW — this file + roadmap.md
├── src/
│   ├── google/agents/cli/   # UNCHANGED — the existing CLI
│   └── agentforge/          # UNCHANGED — parallel source tree
├── extensions/              # UNCHANGED
├── skills/                  # UNCHANGED
├── docs/                    # UNCHANGED
└── README.md, RELEASE_NOTES.md  # patched (small appends only)
```

## See also

- `docs/architecture/roadmap.md` — phase tracker.
- The audit report (project memory) — full 19-section analysis with
  exact Phase 1 file changes.
- The CLI docs under `docs/src/...` — the foundation that this web
  app wraps.
