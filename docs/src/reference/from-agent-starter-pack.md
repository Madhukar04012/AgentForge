# From Agent Starter Pack

`agentforge` is the successor to Agent Starter Pack (ASP). It builds on the same foundation with key improvements.

---

## What Changed

**Coding agent first.** ASP was built for humans running an interactive CLI. agentforge is built for coding agents — with 7 bundled skills that give them deep context about ADK, evaluation, deployment, and observability. Every command still works from the terminal too.

**CLI replaces Makefile.** ASP used `make` targets (`make dev`, `make eval`, `make deploy`). agentforge replaces them with a unified CLI covering the full lifecycle, with flags, help text, and structured output.

**New capabilities.** `agentforge` adds commands that didn't exist in ASP: `playground`, `run`, `deploy`, the full eval surface (`eval generate`, `eval grade`, `eval dataset synthesize`, `eval compare`, `eval analyze`, `eval metric list`, `eval optimize`), `lint`, `login`, and skill management (`setup`, `update`).

### Command Mapping

| Agent Starter Pack | agentforge |
|---|---|
| `create` | `create` (alias for `scaffold create`) |
| `enhance` | `scaffold enhance` |
| `upgrade` | `scaffold upgrade` |
| `setup-cicd` | `infra cicd` |
| `register-gemini-enterprise` | `publish gemini-enterprise` |

### Config Key

The configuration moved from `[tool.agent-starter-pack]` in `pyproject.toml` to a dedicated `agentforge-manifest.yaml`:

**Before (`pyproject.toml`)**
```toml
[tool.agent-starter-pack]
agent_directory = "app"

[tool.agent-starter-pack.create_params]
deployment_target = "cloud_run"
```

**After (`agentforge-manifest.yaml`)**
```yaml
name: my-agent
agent_directory: app
create_params:
  deployment_target: cloud_run
```

### Template Coverage

agentforge supports the `adk` template (Python), with A2A built into every ADK agent — the standalone `adk_a2a` template was merged into `adk`. RAG is a clone-and-study recipe rather than a template (the former `agentic_rag` template was removed; adapt the `rag-vector-search` / `rag-agent-search` samples instead). ASP had additional templates (`adk_go`, `adk_java`, `adk_ts`, `adk_live`, `custom_a2a`) that are not yet available in AgentForge. Support for these is planned.

### What Stays the Same

- **Templates** — same `adk` agent template (RAG is now a clone-and-study recipe), same deployment targets, same session storage options
- **Project structure** — generated projects have the same layout, your `app/agent.py` code is unchanged
- **Terraform** — same infrastructure-as-code under `deployment/terraform/`
- **CI/CD pipelines** — same Cloud Build and GitHub Actions configurations

---

## Migrating an Existing Project

Your existing ASP projects are fully compatible. The only required change is renaming the config section in `pyproject.toml`.

**Step 1: Install agentforge**

```bash
uvx agentforge setup
```

**Step 2: Rename the config section**

```bash
sed -i '' 's/tool.agent-starter-pack/tool.agentforge/g' pyproject.toml
```

The next time config is read, it will trigger a migration to `agentforge-manifest.yaml` and remove the `tool.agentforge` section from `pyproject.toml`.

**Step 3: Verify**

```bash
agentforge info
```

This shows your project config and confirms agentforge can read it. Your agent code, tests, Terraform, and CI/CD pipelines all work as before.

!!! note "Existing eval cases under `tests/eval/evalsets/`?"
    ASP's default agent template shipped a `basic.evalset.json` using the ADK `EvalSet` schema. The eval surface in agentforge reads a different format from `tests/eval/datasets/`. See [Migrating Eval Datasets](eval-dataset-migration.md) for the conversion.
