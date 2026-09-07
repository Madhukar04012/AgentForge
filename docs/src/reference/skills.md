# Skills Reference

Skills are context files installed to coding agents (Antigravity CLI, Claude Code, GitHub Copilot) via `agentforge setup`. They provide domain-specific guidance for working with generated agent projects.

```bash
agentforge setup      # Install all skills
agentforge update     # Reinstall / update skills
```

---

## `agentforge-adk-code`

It provides a quick reference for agent types, tool definitions, orchestration patterns, callbacks, and state management.

---

## `agentforge-deploy`

Covers deployment workflows, service accounts, rollback, and production infrastructure. Part of the Google ADK (Agent Development Kit) skills suite.

---

## `agentforge-eval`

Covers the full evaluation lifecycle: dataset schema, generating traces and grading them, comparing runs, analyzing failure clusters, discovering metrics, prompt optimization, LLM-as-judge configuration, and common failure causes. Part of the Google ADK (Agent Development Kit) skills suite.

---

## `agentforge-observability`

Covers Cloud Trace, prompt-response logging, BigQuery Agent Analytics, third-party integrations (AgentOps, Phoenix, MLflow, etc.), and troubleshooting. Part of the Google ADK (Agent Development Kit) skills suite.

---

## `agentforge-publish`

Covers ADK vs A2A registration modes, programmatic and interactive usage, flag reference, auto-detection from deployment metadata, and troubleshooting. Part of the Google ADK (Agent Development Kit) skills suite.

---

## `agentforge-scaffold`

Covers `agentforge scaffold create`, `scaffold enhance`, and `scaffold upgrade` commands, template options, deployment targets, and the prototype-first workflow.

---

## `agentforge-workflow`

Always active — provides the full workflow (scaffold, build, evaluate, deploy, publish, observe), code preservation rules, model selection guidance, and troubleshooting steps for ADK or any agent development.

---

