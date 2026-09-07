---
name: agentforge-langchain
description: >
  Use when working in this project — adding tools, editing the agent, running,
  evaluating, serving or deploying it — or when guidance mentions ADK, LlmAgent,
  google.adk, adk web, or an ADK runner. This project is LangChain/LangGraph
  scaffolded by agentforge, so ADK-specific instructions do not apply.
---

# LangChain project (agentforge)

The agent is a compiled LangGraph graph exported as `root_agent` from
`app/agent.py`. There is no `google.adk` dependency and no ADK runner. Other
`agentforge-*` skills assume ADK; where they describe the agent itself,
this skill wins.

**Experimental, and Agent Runtime is degraded.** Deploy to cloud_run or gke. On
agent_runtime the app serves, but `publish gemini-enterprise` is refused, the Console
playground cannot invoke it, and Console sessions/traces stay empty: all three want the
ADK `reasoning_engine` routes this project does not serve. Say so before recommending it.

## What ADK guidance maps to here

| ADK guidance | This project |
|---|---|
| `LlmAgent`, `Agent`, `google.adk.tools` | `langchain.agents.create_agent`, plain Python functions as tools, or any compiled `StateGraph` |
| `adk web`, `adk run` | `agentforge playground` (runs `langgraph dev`) |
| ADK runner behind `agentforge run` | `agentforge run` invokes the graph in-process |
| `agentforge eval dataset synthesize`, `eval optimize` | Unavailable: both drive the agent through ADK. The command says so and exits |
| Add an `LlmAgent` in `app/agent.py` | Change the graph in `app/agent.py`; keep the name `root_agent` |

## The contract

Keep these two, whatever you build inside them:

- `app/agent.py` exports `root_agent`, a compiled graph with `messages` state.
  Callers only use `root_agent.invoke({"messages": [...]})` and
  `root_agent.astream(stream_mode="messages")`.
- `app/fast_api_app.py` exposes `app`. Every deployment target runs
  `uvicorn app.fast_api_app:app`.

Adding a tool means writing a typed function with a docstring and passing it in
`tools=[...]`. Switching frameworks (LangGraph `StateGraph`,
`deepagents.create_deep_agent`) means rewriting `app/agent.py` only. Pre-1.0
LangChain (LCEL chains, `AgentExecutor`) is not supported: not compiled graphs.

## Commands

```bash
agentforge install                  # uv sync
agentforge playground               # langgraph dev, port 8080
agentforge run "hello"              # invoke the graph in-process
agentforge eval generate --dataset tests/eval/datasets/basic-dataset.json -o tests/eval/output/
agentforge eval grade --traces tests/eval/output/<dataset>.json --config tests/eval/eval_config.yaml
agentforge deploy                   # unchanged
agentforge scaffold enhance -d cloud_run --cicd-runner github_actions   # add infra later
```

`playground`, `run` and `eval generate` are overridden by
`agentforge-extension.yaml` at the project root. Prefix any command with
`AGENTFORGE_DISABLE_OVERRIDES=1` to reach the built-in instead.

## Serving

A2A only: JSON-RPC at `POST /a2a/app`, card at
`/a2a/app/.well-known/agent-card.json`, health at `/health`. Token streaming
comes from `astream(stream_mode="messages")`.

## Common mistakes

- Renaming `root_agent` or `app`, which breaks `run`, eval and deploy.
- Reaching for `eval dataset synthesize` or `eval optimize`: they need ADK.
  Write cases into `tests/eval/datasets/` and use `eval generate` + `eval grade`.
- Expecting `/run_sse` or ADK session routes; this server serves A2A.
- Running `agentforge run --url ...` against a deployed agent without
  `AGENTFORGE_DISABLE_OVERRIDES=1`, which invokes the local graph instead.
- `run` and `eval generate` call Gemini through Vertex AI with ADC, so they need
  `GOOGLE_CLOUD_PROJECT` and credentials, or `GOOGLE_API_KEY` / `GEMINI_API_KEY`
  in `.env`.

## References

- `references/langchain.md` — framework contract and per-command detail.
- `references/samples.md` — agents worth copying from, by shape.
