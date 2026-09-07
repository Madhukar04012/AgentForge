# Coding Agent Guide

This is a LangChain project, not an ADK one: `app/agent.py`
compiles a LangGraph graph and `app/fast_api_app.py` serves it
over A2A. Read `.agents/skills/agentforge-langchain/SKILL.md` before changing either.

> **Experimental.** Cloud Run and GKE are the supported targets. On Agent Runtime the
> container serves and traces normally, but everything that expects an ADK app is broken,
> because this project serves A2A and no `reasoning_engine` routes:
>
> - `agentforge publish gemini-enterprise` is refused: registration invokes the agent
>   through `:streamQuery`. Publish from a Cloud Run or GKE deployment instead.
> - The Console playground cannot invoke the agent.
> - The Console's session and trace views stay empty (no managed Agent Engine sessions;
>   traces still reach Cloud Trace).

## The loop

1. Build in `app/`, try it with `agentforge playground`
   (LangGraph Studio) or `agentforge run "prompt"`.
2. Write eval cases by hand in `tests/eval/datasets/`, then `agentforge eval run` until it
   holds up. `agentforge eval compare` shows regressions; `agentforge eval analyze` clusters
   failures. `eval dataset synthesize` and `eval optimize` need an ADK agent to introspect,
   so this project refuses them.
3. `uv run pytest tests/unit tests/integration` before deploying.
4. `agentforge deploy` **only after the user approves it.**

## Rules

- Change only what was asked. Keep surrounding code, comments, and config values.
- **Never change the model** unless asked. On a model 404, fix `GOOGLE_CLOUD_LOCATION`
  (try `global`), not the model name.
- Run Python through uv: `uv run python script.py`, after `agentforge install`.
- Same error three times means fix the cause, not retry.
- Terraform 409: `terraform import`, don't recreate.
