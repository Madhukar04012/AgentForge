<div align="center">
  <h1>AgentForge</h1>
  <p>AI Agent Development, Evaluation & Deployment Platform.</p>

  <p>
    <a href="#get-started">Get Started</a> &nbsp;&nbsp;|&nbsp;&nbsp;
    <a href="#agent-skills">Skills</a> &nbsp;&nbsp;|&nbsp;&nbsp;
    <a href="#cli-commands">Commands</a> &nbsp;&nbsp;|&nbsp;&nbsp;
    <a href="https://pypi.org/project/agentforge/">PyPI</a> &nbsp;&nbsp;|&nbsp;&nbsp;
    <a href="https://github.com/Madhukar04012/AgentForge/issues">Issues</a> &nbsp;&nbsp;|&nbsp;&nbsp;
    <a href="https://github.com/Madhukar04012/AgentForge/tree/main/docs">Docs</a> &nbsp;&nbsp;|&nbsp;&nbsp;
    <a href="https://github.com/Madhukar04012/AgentForge/blob/main/RELEASE_NOTES.md">Release Notes</a> &nbsp;&nbsp;|&nbsp;&nbsp;
    <a href="https://github.com/Madhukar04012/AgentForge">Star us</a>
  </p>
</div>

---

> AgentForge is an AI agent development platform for building, evaluating, and deploying production agents.

---

Turn your favorite coding assistant into an expert at building and deploying agents on Google Cloud.

**AgentForge** gives your coding agent the skills and commands to build, scale, govern, and optimize enterprise-grade agents — so you don't have to learn every CLI and service yourself.

**Works seamlessly with:**
[Antigravity CLI](https://antigravity.google/) &nbsp;•&nbsp; [Claude Code](https://docs.anthropic.com/en/docs/claude-code) &nbsp;•&nbsp; [Codex](https://github.com/openai/codex) &nbsp;•&nbsp; *and any other coding agent.*

## Get Started

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/getting-started/installation/), and [Node.js](https://nodejs.org/en/download).

### 1. Install

```bash
uvx agentforge setup
```

<details>
<summary>Or just the skills — your coding agent will handle the rest</summary>

```bash
npx skills add Madhukar04012/AgentForge
```

</details>

### 2. Open your coding agent

Launch [Antigravity CLI](https://antigravity.google/), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [Codex](https://github.com/openai/codex), or any coding agent you prefer.

### 3. Build your first agent

Ask your coding agent to build something — e.g. *"Use AgentForge to build a caveman-style agent that compresses verbose text into terse, technical grunts"*

See the [full tutorial](docs/src/guide/quickstart-tutorial.md) for a step-by-step walkthrough.

**[Browse the full documentation →](docs/)**

---

## Agent Skills

| Skill | What your coding agent learns |
|-------|-------------------------------|
| `agentforge-workflow` | Development lifecycle, code preservation rules, model selection |
| `agentforge-adk-code` | ADK Python API — agents, tools, orchestration, callbacks, state |
| `agentforge-scaffold` | Project scaffolding — `create`, `enhance`, `upgrade` |
| `agentforge-eval` | Evaluation methodology — metrics, datasets, LLM-as-judge, adaptive rubrics |
| `agentforge-deploy` | Deployment — [Agent Runtime](https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale), [Cloud Run](https://cloud.google.com/run), [GKE](https://cloud.google.com/kubernetes-engine), CI/CD, secrets |
| `agentforge-publish` | Gemini Enterprise registration |
| `agentforge-observability` | Observability — Cloud Trace, logging, third-party integrations |

---

## CLI Commands

The primary command is **`agentforge`**. The legacy `agents-cli` binary remains available as a compatibility alias.

| Command | What it does |
|---------|-------------|
| `agentforge setup` | Install CLI + skills to coding agents |
| `agentforge create <name>` | Create a new agent project |
| `agentforge eval run` | Run the agent over the eval dataset and grade the traces |
| `agentforge deploy` | Deploy to Google Cloud |
| `agentforge publish gemini-enterprise` | Register with Gemini Enterprise |

<details>
<summary>See all commands</summary>

| Command | Description |
|---------|-------------|
| `agentforge login` | Authenticate with Google Cloud or AI Studio |
| `agentforge login --status` | Show authentication status |
| **Scaffold** | |
| `agentforge create <name>` | Create a new agent project |
| `agentforge scaffold enhance` | Add deployment or CI/CD to an existing project |
| `agentforge scaffold upgrade` | Upgrade project to a newer AgentForge version |
| **Develop** | |
| `agentforge run "prompt"` | Run agent with a single prompt |
| `agentforge install` | Install project dependencies |
| `agentforge lint` | Run code quality checks (Ruff) |
| **Evaluate** | |
| `agentforge eval run` | Run agent inference and grade the traces |
| `agentforge eval generate` | Run agent inference over eval cases |
| `agentforge eval grade` | Grade generated traces against metrics |
| `agentforge eval dataset synthesize` | Synthesize multi-turn eval scenarios for your local agent |
| `agentforge eval compare` | Compare two eval result files |
| `agentforge eval analyze` | Cluster failure modes from grade results |
| `agentforge eval metric list` | List available metrics |
| `agentforge eval optimize` | Auto-tune agent prompts using eval data |
| **Deploy & Publish** | |
| `agentforge deploy` | Deploy to Google Cloud |
| `agentforge publish gemini-enterprise` | Register with Gemini Enterprise |
| `agentforge infra single-project` | Provision single-project infrastructure |
| `agentforge infra cicd` | Set up CI/CD pipeline + staging/prod infrastructure |
| **Other** | |
| `agentforge info` | Show project config and CLI version |
| `agentforge update` | Force reinstall skills to all IDEs |

</details>

## How it works

<div align="center">
  <a href="https://youtu.be/ECYKo70pPNc">
    Watch the AgentForge demo video
  </a>
</div>

---

## Architecture

The Google Cloud agent stack that AgentForge builds on.

## FAQ

**Is this an alternative to Antigravity CLI, Claude Code, or Codex?**<br>
No. **AgentForge is a tool *for* coding agents, not a coding agent itself.** It provides the CLI commands and skills that make your coding agent better at building, evaluating, and deploying ADK agents on Google Cloud.

**How is this different from just using `adk` directly?**<br>
[ADK](https://adk.dev) is an agent framework. AgentForge gives your coding agent the skills and tools to build, evaluate, and deploy ADK agents end-to-end.

**Do I need Google Cloud?**<br>
For local development (`create`, `run`, `eval`), no — you can use an [AI Studio API key](https://aistudio.google.com/apikey) to run Gemini with [ADK](https://adk.dev) locally. For deployment and cloud features, yes.

**Can I use this with an existing agent project?**<br>
Yes. `agentforge scaffold enhance` adds deployment and CI/CD to existing projects.

**Can I use AgentForge without a coding agent?**<br>
Yes. The CLI works standalone — you can run `agentforge scaffold`, `eval`, `deploy`, and every other command directly from your terminal. The skills just make it easier for coding agents to do it for you.

**How can I extend AgentForge with other skills?**<br>
AgentForge skills cover the agent-building lifecycle (scaffold, ADK code patterns, evals, deploy, publish, observability). For adjacent concerns, you could install another skill suite alongside. For example, [agent-skills](https://github.com/addyosmani/agent-skills) covers general software-engineering workflows (ideation, spec gates, planning, code review), and [google/skills](https://github.com/google/skills) covers Google Cloud foundations (BigQuery, Cloud Run, Firebase, GKE).

## Feedback

We value your input — it helps us improve AgentForge for the community.

- **Bugs & feature requests:** [open an issue](https://github.com/Madhukar04012/AgentForge/issues/new) — 👍 the ones you want prioritized
- **Share what you built:** we'd love to hear about your projects! Reach out at <a href="mailto:agents-cli@google.com">agents-cli@google.com</a> to share your agent or provide feedback

## Terms of Service

AgentForge leverages Google Cloud APIs. When you deploy agents, you'll be deploying resources in your own Google Cloud project and will be responsible for those resources. Please review the [Google Cloud Service Terms](https://cloud.google.com/terms/service-terms) for details.

---

## Web Platform (Phase 1)

A web frontend for the same foundation is landing incrementally. The
CLI is **not** changing — the web app is a thin FastAPI backend + a
React/Vite SPA that wraps the existing eval flywheel, deploy targets,
and ADK-backed agent runtime in a browser experience.

Phase 1 ships only the skeleton (settings, health, login/logout, a
placeholder recruiter demo, and the Docker compose stack). Real
domain endpoints (agents, workflows, executions, evaluations,
deployments) arrive in later phases.

Bring up the local stack:

```bash
docker compose -f docker/docker-compose.yml up
```

Then:

- `http://localhost:8080` — web SPA
- `http://localhost:8000/api/v1/health` — API liveness
- `http://localhost:8000/api/docs` — OpenAPI / Swagger UI

See [`docs/architecture/architecture.md`](docs/architecture/architecture.md)
and [`docs/architecture/roadmap.md`](docs/architecture/roadmap.md)
for the full design and phase tracker.
